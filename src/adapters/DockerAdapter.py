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

# Third party imports
import netaddr
import sh
import docker

# VLEAD imports
import VMUtils
from dict2default import dict2default
from settings import *
import Logging


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


__TAG__ = "DockerAdapter: "
LOG_FILENAME = "/root/ovpl/log/DockerAdapter.log"
Logger = Logging.create_logger(__TAG__, save_path=LOG_FILENAME)

class InvalidVMIDException(Exception):
    def __init__(msg):
        Exception.__init__(msg)


def create_vm(lab_spec, custom_vm_id=""):

    """If no vm_id is specified, it is computed using the last two segments of
    an available IP address; vm_spec is an object """
    def gen_vm_id(custom_id, ip):
        if custom_id == "":
            m = re.match(r'[0-9]+.[0-9]+.([0-9]+).([0-9]+)', ip)
            assert m != None

            return m.group(1) + m.group(2)
        else:
            validate_vm_id(custom_id)
            return custom_id
      

    Logger.debug("create_vm()")

    ip_address = find_available_ip()
    Logger.debug("vm ip: " + str(ip_address))

    vm_id = gen_vm_id(custom_vm_id, ip_address)
    Logger.debug("vm id: " + str(vm_id))


    docker_args = construct_docker_args(ip_address, lab_spec)
    Logger.debug("Docker Arguments: " + str(docker_args))

    #instantiate a docker client
    client = docker.Client()
    container_id = client.create_container(docker_args.os, 
                        command = "true",
                        detach = True,
                        hostname = docker_args.hostname,
                        mem_limit = docker_args.ram)#HACK!docker_args.swap)

    Logger.debug("container id: " + str(container_id))

    return container_id


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
    Logger.debug(" init_vm(): vm_id = %s" % vm_id)
    copy_vm_manager_files(vm_id)
    start_vm_manager(vm_id)
    # Return the VM's IP and port info
    response = {"vm_id": vm_id, "vm_ip": get_vm_ip(vm_id), "vmm_port": VM_MANAGER_PORT}
    Logger.debug(" init_vm(): response = %s" % str(response))
    return response

def copy_vm_manager_files(vm_id):
    Logger.debug(" copy_vm_manager_files(): vm_id = %s" % vm_id)
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    src_dir = current_file_path + VM_MANAGER_SRC_DIR
    dest_dir = "%s%s%s" % (VM_ROOT_DIR, vm_id, VM_MANAGER_DEST_DIR)
    Logger.debug(" copy_vm_manager_files(): dest_dir = %s, src_dir = %s" % (dest_dir, src_dir))
    # Create the destination directory
    #os.makedirs(dest_dir)
    # Copy the files from source directory to dest. dir.
    try:
        shutil.copytree(src_dir, dest_dir)
    except Exception, e:
        Logger.error(" copy_vm_manager_files():  dest_dir = %s, src_dir = %s, ERROR = %s" % \
                              (dest_dir, src_dir, str(e)))


def start_vm_manager(vm_id):
    command = VZCTL + " exec " + vm_id + " \"su - root -c \'python " + \
        VM_MANAGER_DEST_DIR + "/" + VM_MANAGER_SCRIPT + " &\'\""
    Logger.debug(" start_vm_manager(): command = %s" % command)
    try:
        subprocess.check_call(command, stdout=LOG_FD, stderr=LOG_FD, shell=True)
    except Exception, e:
        Logger.error(" start_vm_manager(): command = %s, ERROR = %s" % (cpmmand, str(e)))
        return False

def get_resource_utilization():
    pass

def stop_vm(vm_id):
    vm_id = validate_vm_id(vm_id)
    try:
        subprocess.check_call(VZCTL + " stop " + vm_id, stdout=LOG_FD, stderr=LOG_FD, shell=True)
        return "Success"
    except subprocess.CalledProcessError, e:
        Logger.error("Error stopping VM: " + str(e))
        return "Failed to stop VM: " + str(e)

def destroy_vm(vm_id):
    vm_id = validate_vm_id(vm_id)
    try:
        subprocess.check_call(VZCTL + " stop " + vm_id, stdout=LOG_FD, stderr=LOG_FD, shell=True)
        subprocess.check_call(VZCTL + " destroy " + vm_id, stdout=LOG_FD, stderr=LOG_FD, shell=True)
        return "Success"
    except subprocess.CalledProcessError, e:
        Logger.error("Error destroying VM: " + str(e))
        return "Failed to destroy VM: " + str(e)

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


class DockerArgs:
    def __init__(self, os, ip, diskspace, hostname, nameserver, ram, swap):
        self.os = os
        self.ip = ip
        self.diskspace = diskspace
        self.hostname = hostname
        self.nameserver = nameserver
        self.ram = ram
        self.swap = swap

    def __str__(self):
        return "\n os: " + self.os + \
                "\n ip: " + self.ip + \
                "\n diskapce: " + self.diskspace + \
                "\n hostname: " + self.hostname + \
                "\n nameserver: " + self.nameserver + \
                "\n ram: " + self.ram + \
                "\n swap: " + self.swap + \
                "\n"



def construct_docker_args(ip_address, lab_specz={}):

    def get_vm_spec():
        lab_spec = dict2default(lab_specz)
        vm_spec = { "lab_ID" : lab_spec['lab']['description']['id'],
            "os" : lab_spec['lab']['runtime_requirements']['platform']['os'],
            "os_version" : lab_spec['lab']['runtime_requirements']['platform']['osVersion'],
            "ram" : lab_spec['lab']['runtime_requirements']['platform']['memory']['min_required'],
            "diskspace" : lab_spec['lab']['runtime_requirements']['platform']['storage']['min_required'],
            "swap" : lab_spec['lab']['runtime_requirements']['platform']['memory']['swap']
        }

        Logger.debug("vm spec: %s" % (vm_spec))

        return vm_spec

    vm_spec = get_vm_spec()
    
    lab_ID = get_test_lab_id() if vm_spec["lab_ID"] == "" else vm_spec["lab_ID"]
    host_name = lab_ID + "." + get_adapter_hostname()
    
    os_template = find_os_template(vm_spec["os"], vm_spec["os_version"])
    
    (ram, swap) = VMUtils.get_ram_swap(vm_spec["ram"], vm_spec["swap"])
    (disk_soft, disk_hard) = VMUtils.get_disk_space(vm_spec["diskspace"])
    

    return DockerArgs(os_template, 
                        find_available_ip(), 
                        disk_soft, 
                        host_name, 
                        get_adapter_nameserver(),
                        ram, 
                        swap)



#returns a free ip as a string for a container to bind to.
def find_available_ip():
    #try and ping. if the IP does not respond, (gives wrong return code) return the IP as free
    def is_ip_free(ip):
        try:
            sh.ping(str(ip), c=1)
        except sh.ErrorReturnCode:
            return True

        return False

    def is_ip_usable(ip):
            #reject IP's like  192.0.2.0 or 192.0.2.255 for subnet 192.0.2.0/24
            return not (ip == ip_network.network or ip == ip_network.broadcast)

    for subnet in get_subnet():
        ip_network = netaddr.IPNetwork(subnet)
        ip_addrs = list(ip_network)

        for ip in ip_addrs:
            if is_ip_usable(ip) and is_ip_free(ip):
                return str(ip)

    raise Exception("unable to find free ip in subnet ", get_subnet())
    return None

def find_os_template(os, os_version):
    # What to do when request comes for unavailable OS/version?
    os = get_test_os().upper() if os == "" else os.strip().upper()
    os_version = get_test_os_version() if os_version == "" else os_version.strip()
    
   
    OS_MAPPING = {("UBUNTU", "12.04") : "ubuntu:12.04",
                   ("UBUNTU", "12") : "ubuntu:12.04"}
    #TODO: populate list

    if (os, os_version) in OS_MAPPING:
        Logger.debug("os: " + os + " | version: " + os_version)
        return OS_MAPPING[(os, os_version)]
    else:
        Logger.error("unable to find OS template. os: ", os, " |os version: ", os_version)

    # if os == "UBUNTU":
    #     if os_version == "12.04" or os_version == "12":
    #         return "ubuntu-12.04-custom-x86_64"
    #     elif os_version == "11.10" or os_version == "11":
    #         return "ubuntu-11.10-x86_64"
    # elif os == "CENTOS":
    #     if os_version == "6.3":
    #         return "centos-6.3-x86_64"
    #     elif os_version == "6.2":
    #         return "centos-6.2-x86_64"
    # elif os == "DEBIAN":
    #     if os_version == "6.0" or os_version == "6":
    #         return "debian-6.0-x86_64"
    # else:
    #     pass

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


def test():
    #vm_spec = VMSpec.VMSpec({'lab_ID': 'test99'})
    import json
    lab_spec = json.loads(open("sample_lab_spec.json").read())
    create_vm(lab_spec)
    create_vm(lab_spec, "99100")
   
    destroy_vm("99100")
   

def test_logging():
    Logger.debug(" test_logging()")

setup_logging()
LOG_FD = open(LOG_FILENAME, 'a')

if __name__ == "__main__":
    # Start an HTTP server and wait for invocation
    # Parse the invocation command and route to 
    # appropriate methods.
    test()