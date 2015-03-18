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
import __init__
import re
import os
import shutil
from exceptions import Exception

# Third party imports
import netaddr
import sh

# VLEAD imports
import VMUtils
from dict2default import dict2default
import settings
import BaseAdapter
from http_logging.http_logger import logger
from utils.git_commands import *
from utils.envsetup import EnvSetUp
from utils.execute_commands import *

class InvalidVMIDException(Exception):
    def __init__(msg):
        Exception.__init__(msg)


class AWSAdapter(object):

    def create_vm(self, lab_spec, vm_id=""):
        logger.debug("AWSAdapter: create_vm()")

        (vm_create_args, vm_set_args) = construct_vzctl_args(lab_spec)

        logger.debug("CentOSVZAdapter: create_vm(): ip = %s, vm_id = %s, vm_create_args = %s, vm_set_args = %s" % \
                              (ip_address, vm_id, vm_create_args, vm_set_args))
        try:
            (ret_code, output) = execute_command(VZCTL + " create " + vm_id + vm_create_args)
            if ret_code == 0:
                (ret_code,output) = execute_command(VZCTL + " start " + vm_id)
            if ret_code == 0:
                (ret_code, output) = execute_command(VZCTL + " set " + vm_id + vm_set_args)
            if ret_code == 0:
                return ip_address
        except Exception, e:
            logger.error("Error creating VM: " + str(e))
            #raise e
            return 105 

    def init_vm(self, vm_id, lab_repo_name):
        logger.debug("CentOSVZAdapter: init_vm(): vm_id = %s" % vm_id)
        success = True
        success = success and  copy_ovpl_source(vm_id)
        success = success and copy_lab_source(vm_id, lab_repo_name)
        success = success and self.start_vm_manager(vm_id)
        # Return the VM's IP and port info
        response = {"vm_id": vm_id, "vm_ip": get_vm_ip(vm_id), "vmm_port": settings.VM_MANAGER_PORT}
        logger.debug("CentOSVZAdapter: init_vm(): success = %s, response = %s" % (success, response))
        return (success, response)

    def destroy_vm(self, vm_id):
        vm_id = validate_vm_id(vm_id)
        try:
            execute_command(VZCTL + " stop " + vm_id)
            execute_command(VZCTL + " destroy " + vm_id)
            return "Success"
        except Exception, e:
            logger.error("Error destroying VM: " + str(e))
            return "Failed to destroy VM: " + str(e)

    def restart_vm(self, vm_id):
        vm_id = validate_vm_id(vm_id)
        try:
            execute_command(VZCTL + " restart " + vm_id)
        except Exception, e:
            raise e
        return start_vm_manager(vm_id)

    def start_vm(self, vm_id):
        self.restart_vm(self, vm_id) #HACK

    
    def start_vm_manager(self, vm_id):
        command = VZCTL + " exec " + str(vm_id) + " \"su - root -c \'python " + \
            settings.VMMANAGERSERVER_PATH + settings.VM_MANAGER_SCRIPT + " &\'\""
        logger.debug("CentOSVZAdapter: start_vm_manager(): command = %s" % command)
        try:
            execute_command(command)
            return True
        except Exception, e:
            logger.error("CentOSVZAdapter: start_vm_manager(): command = %s, ERROR = %s" % (command, str(e)))
            return False

    def get_resource_utilization(self):
        pass

    def stop_vm(self, vm_id):
        vm_id = validate_vm_id(vm_id)
        try:
            execute_command(VZCTL + " stop " + vm_id)
            return "Success"
        except Exception, e:
            logger.error("Error stopping VM: " + str(e))
            return "Failed to stop VM: " + str(e)

    def test_logging(self):
        logger.debug("CentOSVZAdapter: test_logging()")

    def is_running_vm(self, vm_id):
        vm_id = validate_vm_id(vm_id)
        pass

    def migrate_vm(self, vm_id, destination):
        vm_id = validate_vm_id(vm_id)
        pass

    def take_snapshot(self, vm_id):
        vm_id = validate_vm_id(vm_id)
        pass


def copy_files(src_dir, dest_dir):

    try:
        command = "rsync -arz --progress " + src_dir + " " + dest_dir
        logger.debug("Command = %s" % command)
        (ret_code, output) = execute_command(command)
        if ret_code == 0:
            logger.debug("Copy successful")
            return True
        else:
            logger.debug("Copy Unsuccessful, return code is %s" % str(ret_code))
            return False
    except Exception, e:
        logger.error("ERROR = %s" % str(e))
        return False

def copy_ovpl_source(ip_addr):
    env = EnvSetUp()
    src_dir =     env.get_ovpl_directory_path()
    dest_dir = "%s%s%s%s%s" % ("root@", ip_addr, ":", settings.VM_DEST_DIR, "ovpl/")
    logger.debug("ip_address = %s, src_dir=%s, dest_dir=%s" % (ip_addr, src_dir, dest_dir))
    try:
        return copy_files(src_dir, dest_dir)
    except Exception, e:
        logger.error("ERROR = %s" % str(e))
        return False

def copy_lab_source(vm_id, lab_repo_name):

    src_dir =     GIT_CLONE_LOC[:-1] + "/" + lab_repo_name
    dest_dir = "%s%s%s%s%s" % ("root@", ip_addr, ":", settings.VM_DEST_DIR, "labs/")
    logger.debug("ip_address = %s, src_dir=%s, dest_dir=%s" % (ip_addr, src_dir, dest_dir))
    try:
        return copy_files(src_dir, dest_dir)
    except Exception, e:
        logger.error("ERROR = %s" % str(e))
        return False
        
def construct_vzctl_args(lab_specz={}):
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
    lab_ID = settings.get_test_lab_id() if vm_spec["lab_ID"] == "" else vm_spec["lab_ID"]
    host_name = lab_ID + "." + settings.get_adapter_hostname()
    os_template = find_os_template(vm_spec["os"], vm_spec["os_version"])
    (ram, swap) = VMUtils.get_ram_swap(vm_spec["ram"], vm_spec["swap"])
    (disk_soft, disk_hard) = VMUtils.get_disk_space(vm_spec["diskspace"])
    vm_create_args = " --ostemplate " + os_template + \
                     " --ipadd " + ip_address + \
                     " --diskspace " + disk_soft + ":" + disk_hard + \
                     " --hostname " + host_name
    # Note to self: check ram format "0:256M" vs "256M"
    vm_set_args = " --nameserver " + settings.get_adapter_nameserver() + \
                  " --ram " + ram + \
                  " --swap " + swap + \
                  " --onboot yes" + \
                  " --save"
    return (vm_create_args, vm_set_args)


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

if __name__ == "__main__":

    # Start an HTTP server and wait for invocation
    # Parse the invocation command and route to 
    # appropriate methods.
    #test()
    if copy_ovpl_source(584):
        logger.debug("test Successful")
    else:
        logger.debug("test UNSuccessful")
