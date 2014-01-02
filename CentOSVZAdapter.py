# Author: Chandan Gupta
# Contact: chandan@vlabs.ac.in

""" A module for managing VMs on CentOS - OpenVZ platform. """

__all__ = [
    'create_vm',
    'start_vm',
    'stop_vm',
    'restart_vm',
    'start_vm_manager',
    'destroy_vm',
    'is_running_vm',
    'migrate_vm',
    'get_resource_utilization',
    'take_snapshot',
    'InvalidVMIDException',
    ]

# Standard Library imports
import re
import subprocess
from exceptions import Exception

# Third party imports
import netaddr

# VLEAD imports
import VMSpec
import VMUtils
import VMManager

# UGLY DUCK PUNCHING: Backporting check_output from 2.7 to 2.6
if "check_output" not in dir(subprocess):
    def f(*popenargs, **kwargs):
        if 'stdout' in kwargs:
            raise ValueError('stdout argument not allowed, it will be overridden.')
        process = subprocess.Popen(stdout=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            raise subprocess.CalledProcessError(retcode, cmd)
        return output
    subprocess.check_output = f


# Globals
NAME_SERVER = "10.10.10.10"
SUBNET = ["10.1.10.0/24", "10.1.11.0/24"]
VZCTL = "/usr/sbin/vzctl"
VZLIST = "/usr/sbin/vzlist -a"
HOST_NAME = "vlabs.ac.in"
LAB_ID = "engg01"
MAX_VM_ID = 2147483644      # 32-bit; exact value based on trial-and-error
VM_MANAGER_PORT = 8089
VM_MANAGER_DIR = "/root/vm_manager"
OS = "Ubuntu"
OS_VERSION = "12.04"
IP_ADDRESS_REGEX = "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"
#IP_ADDRESS_REGEX = 
# "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$";

class InvalidVMIDException(Exception):
    def __init__(msg):
        Exception.__init__(msg)


def create_vm(vm_id, vm_spec):
    """ VM_specification is a VMSpec object """
    # Create the VM
    vm_id = validate_vm_id(vm_id)
    (vm_create_args, vm_set_args) = construct_vzctl_args(vm_spec)
    try:
        subprocess.check_call(VZCTL + " create " + vm_id + vm_create_args, shell=True)
        subprocess.check_call(VZCTL + " start " + vm_id, shell=True)
        subprocess.check_call(VZCTL + " set " + vm_id + vm_set_args, shell=True)
    except subprocess.CalledProcessError, e:
        raise e
    return start_vm_manager(vm_id)

def restart_vm(vm_id):
    vm_id = validate_vm_id(vm_id)
    try:
        subprocess.check_call(VZCTL + " restart " + vm_id, shell=True)
    except subprocess.CalledProcessError, e:
        raise e
    return start_vm_manager(vm_id)

# Function alias
start_vm = restart_vm

def start_vm_manager(vm_id):
    # Copy the VMManager package to the VM
    # Start the VMManager on a chosen port
    # 
    # Return the VM's IP and port info
    return (get_vm_ip(vm_id), VM_MANAGER_PORT)

def get_resource_utilization():
    pass

def stop_vm(vm_id):
    vm_id = validate_vm_id(vm_id)
    try:
        subprocess.check_call(VZCTL + " stop " + vm_id, shell=True)
    except subprocess.CalledProcessError, e:
        raise e
    # Return success or failure

def destroy_vm(vm_id):
    vm_id = validate_vm_id(vm_id)
    try:
        subprocess.check_call(VZCTL + " stop " + vm_id, shell=True)
        subprocess.check_call(VZCTL + " destroy " + vm_id, shell=True)
    except subprocess.CalledProcessError, e:
        raise e
    # Return success or failure

def is_running_vm(vm_id):
    vm_id = validate_vm_id(vm_id)
    pass

def get_vm_ip(vm_id):
    vm_id = validate_vm_id(vm_id)
    try:
        vzlist = subprocess.check_output(VZLIST + " | grep " + vm_id, shell=True)
        if vzlist == "":
            return                                  # raise exception?
        ip_address = re.match(r'[\s*\w+]*\s+(%s)' % IP_ADDRESS_REGEX, vzlist)
        if ip_address != None:
            ip_address = ip_address.group(0)
        return ip_address
    except subprocess.CalledProcessError, e:
        raise e

def migrate_vm(vm_id, destination):
    vm_id = validate_vm_id(vm_id)
    pass

def take_snapshot(vm_id):
    vm_id = validate_vm_id(vm_id)
    pass

def construct_vzctl_args(vm_spec):
    """ Returns a tuple of vzctl create arguments and set arguments """
    lab_ID = LAB_ID if vm_spec.lab_ID == "" else vm_spec.lab_ID
    host_name = lab_ID + "." + HOST_NAME
    ip_address = find_available_ip()
    os_template = find_os_template(vm_spec.os, vm_spec.os_version)
    (ram, swap) = VMUtils.get_ram_swap(vm_spec.ram, vm_spec.swap)
    (disk_soft, disk_hard) = VMUtils.get_disk_space(vm_spec.diskspace)
    vm_create_args = " --ostemplate " + os_template + \
                     " --ipadd " + ip_address + \
                     " --diskspace " + disk_soft + ":" + disk_hard + \
                     " --hostname " + host_name
    # Note to self: check ram format "0:256M" vs "256M"
    vm_set_args = " --nameserver " + NAME_SERVER + \
                  " --ram " + ram + \
                  " --swap " + swap + \
                  " --onboot yes" + \
                  " --save"
    return (vm_create_args, vm_set_args)

def find_available_ip():
    # not designed to be concurrent?
    used_ips = subprocess.check_output(VZLIST, shell=True)
    for subnet in SUBNET:
        ip_network = netaddr.IPNetwork(subnet)
        for ip in list(ip_network):
            if ip == ip_network.network or ip == ip_network.broadcast:
                # e.g. 192.0.2.0 or 192.0.2.255 for subnet 192.0.2.0/24
                continue
            else:
                ip_address = str(ip)
                if ip_address not in used_ips:
                    return ip_address

def find_os_template(os, os_version):
    # What to do when request comes for unavailable OS/version?
    os = OS.upper() if os == "" else os.strip().upper()
    os_version = OS_VERSION if os_version == "" else os_version.strip()
    if os == "UBUNTU":
        if os_version == "12.04" or os_version == "12":
            return "ubuntu-12.04-x86_64"
        elif os_version == "11.10" or os_version == "11":
            return "ubuntu-11.10-x86_64"
    elif os == "CENTOS":
        if os_version == "6.3":
            return "centos-6.3-x86_64"
        elif os_version == "6.2":
            return "centos-6.2-x86_64"
    elif os == "DEBIAN":
        if os_version == "6.0" or os_version == "6":
            return "debian-6.0-x86_64"
    else:
        pass

def validate_vm_id(vm_id):
    vm_id = str(vm_id).strip()
    m = re.match(r'^([0-9]+)$', vm_id)
    if m == None:
        raise InvalidVMIDException("Invalid VM ID.  VM ID must be numeric.")
    vm_id = int(m.group(0))
    if vm_id <= 100:
        raise InvalidVMIDException("Invalid VM ID.  VM ID must be greater than 100.")
    if vm_id > MAX_VM_ID:
        raise InvalidVMIDException("Invalid VM ID.  Specify a smaller VM ID.")
    return str(vm_id)


if __name__ == "__main__":
    # Start an HTTP server and wait for invocation
    # Parse the invocation command and route to 
    # appropriate methods.
    vm_spec = VMSpec.VMSpec()
    create_vm("99100", vm_spec)
    create_vm("99101", vm_spec)
    #create_vm("99102", vm_spec)
    #create_vm("99103", vm_spec)
    destroy_vm("99100")
    destroy_vm("99101")
    #destroy_vm("99102")
    #destroy_vm("99103")
