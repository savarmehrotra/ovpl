# Author: Chandan Gupta
# Contact: chandan@vlabs.ac.in

""" A module for managing VMs on CentOS - OpenVZ platform. """

""" Open issues with the current version:
    1. Not designed for concurrent use e.g. find_available_ip uses vzlist for 
        finding available ip, but if a vm is in the process of being created,
        vzlist will probably not list it, resulting in duplicate ip address.
        These functionalities should be moved up to VMPool for enabling 
        concurrency.
    2. Very little of any kind of error handling is done.
    3. Logging has not been implemented yet.
"""

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
import os
import shutil
from exceptions import Exception
import logging
from logging.handlers import TimedRotatingFileHandler

# Third party imports
import netaddr

# VLEAD imports
import VMUtils
from dict2default import *
from settings import *

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
VZCTL = "/usr/sbin/vzctl"
VZLIST = "/usr/sbin/vzlist -a"
IP_ADDRESS_REGEX = r"[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}"
#IP_ADDRESS_REGEX = 
# "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$";
CENTOSVZ_LOGGER = logging.getLogger('CENTOSVZ')
LOG_FILENAME = '/root/ovpl/log/centosvzadapter.log'


class InvalidVMIDException(Exception):
    def __init__(msg):
        Exception.__init__(msg)


def create_vm(lab_spec, vm_id=""):
    """If no vm_id is specified, it is computed using the last two segments of
       an available IP address; vm_spec is an object """
    if vm_id == "":
        ip_address = find_available_ip()
        m = re.match(r'[0-9]+.[0-9]+.([0-9]+).([0-9]+)', ip_address)
        if m != None:
            vm_id = m.group(1) + m.group(2)
    else:
        vm_id = validate_vm_id(vm_id)
    (vm_create_args, vm_set_args) = construct_vzctl_args(lab_spec)
    try:
        subprocess.check_call(VZCTL + " create " + vm_id + vm_create_args, stdout=LOG_FD, stderr=LOG_FD, shell=True)
        subprocess.check_call(VZCTL + " start " + vm_id, stdout=LOG_FD, stderr=LOG_FD, shell=True)
        subprocess.check_call(VZCTL + " set " + vm_id + vm_set_args, stdout=LOG_FD, stderr=LOG_FD, shell=True)
        return init_vm(vm_id)
    except subprocess.CalledProcessError, e:
        #raise e
        CENTOSVZ_LOGGER.error("Error creating VM: " + str(e))
        return (None, None, None)

def restart_vm(vm_id):
    vm_id = validate_vm_id(vm_id)
    try:
        subprocess.check_call(VZCTL + " restart " + vm_id, stdout=LOG_FD, stderr=LOG_FD, shell=True)
    except subprocess.CalledProcessError, e:
        raise e
    return start_vm_manager(vm_id)

# Function alias
start_vm = restart_vm

def init_vm(vm_id):
    copy_vm_manager_files(vm_id)
    start_vm_manager(vm_id)
    # Return the VM's IP and port info
    response = {"vm_id": vm_id, "vm_ip": get_vm_ip(vm_id), "vm_port": VM_MANAGER_PORT}
    return response

def copy_vm_manager_files(vm_id):
    dest_dir = "%s%s%s" % (VM_ROOT_DIR, vm_id, VM_MANAGER_DEST_DIR)
    # Create the destination directory
    #os.makedirs(dest_dir)
    # Copy the files from source directory to dest. dir.
    shutil.copytree(VM_MANAGER_SRC_DIR, dest_dir)

def start_vm_manager(vm_id):
    command = VZCTL + " exec " + vm_id + " python " + \
        VM_MANAGER_DEST_DIR + "/" + VM_MANAGER_SCRIPT + " &"
    try:
        subprocess.check_call(command, stdout=LOG_FD, stderr=LOG_FD, shell=True)
    except Exception, e:
        CENTOSVZ_LOGGER.error("Error starting vm manager: " + str(e))
        return False
    

def get_resource_utilization():
    pass

def stop_vm(vm_id):
    vm_id = validate_vm_id(vm_id)
    try:
        subprocess.check_call(VZCTL + " stop " + vm_id, stdout=LOG_FD, stderr=LOG_FD, shell=True)
    except subprocess.CalledProcessError, e:
        raise e
    # Return success or failure

def destroy_vm(vm_id):
    vm_id = validate_vm_id(vm_id)
    try:
        subprocess.check_call(VZCTL + " stop " + vm_id, stdout=LOG_FD, stderr=LOG_FD, shell=True)
        subprocess.check_call(VZCTL + " destroy " + vm_id, stdout=LOG_FD, stderr=LOG_FD, shell=True)
    except subprocess.CalledProcessError, e:
        raise e
    # Return success or failure

def is_running_vm(vm_id):
    vm_id = validate_vm_id(vm_id)
    pass

def get_vm_ip(vm_id):
    vm_id = validate_vm_id(vm_id)
    try:
        vzlist = subprocess.check_output(VZLIST + " | grep " + vm_id, stderr=LOG_FD, shell=True)
        if vzlist == "":
            return                                  # raise exception?
        ip_address = re.search(IP_ADDRESS_REGEX, vzlist)
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

def construct_vzctl_args(lab_specz):
    """ Returns a tuple of vzctl create arguments and set arguments """

    def get_vm_spec():
        lab_spec = dict2default(lab_specz)
        vm_spec = { "lab_ID" : lab_spec['lab']['description']['id'],
            "os" : lab_spec['lab']['runtime_requirements']['platform']['os'],
            "os_version" : lab_spec['lab']['runtime_requirements']['platform']['osVersion'],
            "ram" : lab_spec['lab']['runtime_requirements']['platform']['memory']['min_required'],
            "diskspace" : lab_spec['lab']['runtime_requirements']['platform']['storage']['min_required'],
            "swap" : lab_spec['lab']['runtime_requirements']['platform']['memory']['swap']
        }
        return vm_spec

    vm_spec = get_vm_spec()
    lab_ID = LAB_ID if vm_spec["lab_ID"] == "" else vm_spec["lab_ID"]
    host_name = lab_ID + "." + HOST_NAME
    ip_address = find_available_ip()
    os_template = find_os_template(vm_spec["os"], vm_spec["os_version"])
    (ram, swap) = VMUtils.get_ram_swap(vm_spec["ram"], vm_spec["swap"])
    (disk_soft, disk_hard) = VMUtils.get_disk_space(vm_spec["diskspace"])
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
    used_ips = subprocess.check_output(VZLIST, stderr=LOG_FD, shell=True)
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
    # Raise an exception if no available_ip found?

def find_os_template(os, os_version):
    # What to do when request comes for unavailable OS/version?
    os = OS.upper() if os == "" else os.strip().upper()
    os_version = OS_VERSION if os_version == "" else os_version.strip()
    if os == "UBUNTU":
        if os_version == "12.04" or os_version == "12":
            return "ubuntu-12.04-custom-x86_64"
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

def setup_logging():
    CENTOSVZ_LOGGER.setLevel(logging.DEBUG)   # make log level a setting
    # Add the log message handler to the logger
    myhandler = TimedRotatingFileHandler(
                                LOG_FILENAME, when='midnight', backupCount=5)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %I:%M:%S %p')
    myhandler.setFormatter(formatter)
    CENTOSVZ_LOGGER.addHandler(myhandler)


def test():
    #vm_spec = VMSpec.VMSpec({'lab_ID': 'test99'})
    import json
    lab_spec = json.loads(open("sample_lab_spec.json").read())
    create_vm(lab_spec)
    create_vm(lab_spec, "99100")
    #create_vm(vm_spec, "99101")
    #create_vm("99102", vm_spec)
    #create_vm("99103", vm_spec)
    destroy_vm("99100")
    #destroy_vm("99101")
    #destroy_vm("99102")
    #destroy_vm("99103")    

setup_logging()
LOG_FD = open(LOG_FILENAME, 'a')
if __name__ == "__main__":
    # Start an HTTP server and wait for invocation
    # Parse the invocation command and route to 
    # appropriate methods.
    test()
