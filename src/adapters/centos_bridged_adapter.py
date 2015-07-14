""" A module for managing VMs on CentOS -
OpenVZ platform (BridgeVZAdapter). """

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
from __init__ import *
import re
import os
import shutil
from exceptions import Exception

# Third party imports
import netaddr
import sh
import sys
import fileinput

# VLEAD imports
import vm_utils
from dict2default import dict2default
from config.adapters import centosvz_bridge_config as config
from config.adapters import base_config
import base_adapter
from httplogging.http_logger import logger
from utils.git_commands import GitCommands
from utils.envsetup import EnvSetUp
from utils.execute_commands import execute_command

# Globals
VZCTL = "/usr/sbin/vzctl"
VZLIST = "/usr/sbin/vzlist -a"
IP_ADDRESS_REGEX = r"[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}"
#IP_ADDRESS_REGEX =
# "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$";
IP_ADDRESS = None

class OSNotFound(Exception):
    """
    use this exception class to raise an exception when a suitable OS is not
    found
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)

class InvalidVMIDException(Exception):
    def __init__(msg):
        Exception.__init__(msg)


class CentOSBridgeVZAdapter(object):
    def __init__(self):
        self.env = EnvSetUp.Instance()
        self.git = GitCommands()
    """
    Every newly created container needs to be set with IP_ADDRESS in the interfaces file.
    This acheived by modifying the x.x.x.x variable in the template file with the container IP_ADDRESS
    and then copying it to /etc/network/interfaces.
    """
    def prepare_vm_for_bridged_network(self, vm_id):
        src_dirc = base_adapter.OVPL_DIR_PATH + config.BRIDGE_NETWORK_SETUP_PATH + "bridge-settings"
        dest_dirc = base_adapter.OVPL_DIR_PATH + config.BRIDGE_NETWORK_SETUP_PATH + "interfaces"

        try:
            copy_command = "rsync -arz --progress " + src_dirc + " " + dest_dirc
            logger.debug("copy command = %s" % copy_command)
            command = ('%s' % (copy_command))
            logger.debug("Command = %s" % command)
            (ret_code, output) = execute_command(command)
            if ret_code == 0:
                logger.debug("Copy successful")
            else:
                logger.debug("Copy Unsuccessful, return code is %s" % str(ret_code))
        except Exception, e:
            logger.error("ERROR = %s" % str(e))

        textToSearch = 'x.x.x.x'
        textToReplace = IP_ADDRESS
        fileToSearch  = dest_dirc
        fd = open( fileToSearch, 'r+' )
        for line in fileinput.input( fileToSearch ):
            fd.write( line.replace( textToSearch, textToReplace ) )
        fd.close()

        src_dir = "/vz/private/" + base_config.ADS_SERVER_VM_ID + base_adapter.OVPL_DIR_PATH + config.BRIDGE_NETWORK_SETUP_PATH + "interfaces"
        dest_dir = "/vz/private/" + vm_id + "/etc/network/interfaces"
        logger.debug("vm_id = %s, src_dir=%s, dest_dir=%s" % (vm_id, src_dir, dest_dir))
        try:
            return copy_files(str(src_dir), str(dest_dir))
        except Exception, e:
            logger.error("ERROR = %s" % str(e))
            return False


    def create_container(self, vm_id, vm_create_args):
        try:
            command = (r'ssh -o "%s" %s "%s create %s %s"' %
                        (base_config.NO_STRICT_CHECKING, base_config.BASE_IP_ADDRESS,
                         VZCTL, vm_id, vm_create_args))
            logger.debug("BridgeVZAdapter: vm_create(): create command = %s" %
                         command)

            (ret_code, output) = execute_command(command)

            if ret_code == 0:
                return True
            else:
                return False

        except Exception, e:
            logger.error("Error creating VM: " + str(e))
            return False

    def set_container_params(self, vm_id, vm_set_args):
        try:
            command = (r'ssh -o "%s" %s "%s set %s %s"' %
                       (base_config.NO_STRICT_CHECKING,
                        base_config.BASE_IP_ADDRESS,
                        VZCTL, vm_id, vm_set_args))
            logger.debug("BridgeVZAdapter: set_container_params(): set command = %s" %
                         command)
            (ret_code,output) = execute_command(command)
            if ret_code == 0:
                return self.prepare_vm_for_bridged_network(vm_id)
            else:
                return False
        except Exception, e:
            logger.error("Error setting VM: " + str(e))
            return False

    def start_container(self, vm_id):
        try:
            command = (r'ssh -o "%s" %s "%s start %s"' %
                       (base_config.NO_STRICT_CHECKING,
                        base_config.BASE_IP_ADDRESS,
                        VZCTL, vm_id))
            logger.debug("BridgeVZAdapter: start_container(): start command = %s" %
                         command)
            (ret_code, output) = execute_command(command)
            if ret_code == 0:
                return True
            else:
                return False
        except Exception, e:
            logger.error("Error starting VM: " + str(e))
            return False


    def create_vm(self, lab_spec, vm_id=""):
        logger.debug("BridgeVZAdapter: create_vm()")

        vm_id = create_vm_id(vm_id)

        (vm_create_args, vm_set_args) = construct_vzctl_args(lab_spec)

        logger.debug("BridgeVZAdapter: create_vm(): ip = %s, vm_id = %s, vm_create_args = %s, vm_set_args = %s" %
                        (IP_ADDRESS, vm_id, vm_create_args, vm_set_args))

        success = True
        success = success and self.create_container(vm_id, vm_create_args)
        success = success and self.set_container_params(vm_id, vm_set_args)
        success = success and self.start_container(vm_id)
        return (success, vm_id)

    def init_vm(self, vm_id, lab_repo_name):
        logger.debug("BridgeVZAdapter: init_vm(): vm_id = %s" % vm_id)
        success = True
        success = success and copy_public_key(vm_id)
        success = success and copy_ovpl_source(vm_id)
        success = success and copy_lab_source(vm_id, lab_repo_name, self.git.get_git_clone_loc())
        success = success and self.start_vm_manager(vm_id)
        # Return the VM's IP and port info
        response = {"vm_id": vm_id, "vm_ip": IP_ADDRESS,
                    "vm_port": base_config.VM_MANAGER_PORT}
        logger.debug("BridgeVZAdapter: init_vm(): success = %s, response = %s" %
                        (success, response))
        return (success, response)

    def destroy_vm(self, vm_id):
        vm_id = validate_vm_id(vm_id)
        try:

            command = (r'ssh -o "%s" %s "%s stop %s"' %
                        (base_config.NO_STRICT_CHECKING,
                        base_config.BASE_IP_ADDRESS,
                        VZCTL, vm_id))
            logger.debug("BridgeVZAdapter: destroy_vm(): stop command = %s" %
                            command)
            (ret_code,output) = execute_command(command)

            if ret_code == 0:
                command = (r'ssh -o "%s" %s "%s destroy %s"' %
                            (base_config.NO_STRICT_CHECKING,
                            base_config.BASE_IP_ADDRESS,
                            VZCTL, vm_id))
                logger.debug("BridgeVZAdapter: destroy_vm(): destroy command = %s" %
                                command)
                (ret_code,output) = execute_command(command)
                if ret_code == 0:
                    return "Success"
        except Exception, e:
            logger.error("Error destroying VM: " + str(e))
            return "Failed to destroy VM: " + str(e)

    def restart_vm(self, vm_id):
        vm_id = validate_vm_id(vm_id)
        try:
            command = (r'ssh -o "%s" %s "%s restart %s"' %
                        (base_config.NO_STRICT_CHECKING,
                        base_config.BASE_IP_ADDRESS,
                        VZCTL, vm_id))
            logger.debug("BridgeVZAdapter: restart_vm(): restart command = %s" %
                            command)
            (ret_code,output) = execute_command(command)
        except Exception, e:
            raise e
        return start_vm_manager(vm_id)

    def start_vm(self, vm_id):
        self.restart_vm(self, vm_id) #HACK


    def start_vm_manager(self, vm_id):
        ovpl_dir_name = base_adapter.OVPL_DIR_PATH.split("/")[-1]
        vm_ovpl_path = base_config.VM_DEST_DIR + ovpl_dir_name
        start_vm_manager_command = ("python %s%s %s" %
                                    (vm_ovpl_path,
                                     base_config.VM_MANAGER_SERVER_PATH,
                                     ">>/root/vm.log 2>&1 </dev/null &" ))
        command = (r"ssh -o '%s' %s%s '%s'" %
                    (base_config.NO_STRICT_CHECKING,
                    "root@", IP_ADDRESS,
                    start_vm_manager_command))
        logger.debug("BridgeVZAdapter: start_vm_manager(): command = %s" %
                        command)
        try:
            (ret_code,output) = execute_command(command)
            return True
        except Exception, e:
            logger.error("BridgeVZAdapter: start_vm_manager(): command = %s, ERROR = %s" %
                            (command, str(e)))
            return False

    def get_resource_utilization(self):
        pass

    def stop_vm(self, vm_id):
        vm_id = validate_vm_id(vm_id)
        try:
            command = (r'ssh -o "%s" %s "%s stop %s"' %
                        (base_config.NO_STRICT_CHECKING,
                        base_config.BASE_IP_ADDRESS,
                        VZCTL, vm_id))
            logger.debug("BridgeVZAdapter: stop_vm(): command = %s" %
                            command)
            (ret_code,output) = execute_command(command)
            return "Success"

        except Exception, e:
            logger.error("Error stopping VM: " + str(e))
            return "Failed to stop VM: " + str(e)

    def test_logging(self):
        logger.debug("BridgeVZAdapter: test_logging()")

    def is_running_vm(self, vm_id):
        vm_id = validate_vm_id(vm_id)
        pass

    def migrate_vm(self, vm_id, destination):
        vm_id = validate_vm_id(vm_id)
        pass

    def take_snapshot(self, vm_id):
        vm_id = validate_vm_id(vm_id)
        pass

def copy_public_key(vm_id):

    try:
        public_key_file = ("%s%s%s%s" %
                            (base_config.VM_ROOT_DIR, base_config.ADS_SERVER_VM_ID,
                            base_config.VM_DEST_DIR, ".ssh/id_rsa.pub"))

        authorized_key_file = ("%s%s%s%s" %
                                (base_config.VM_ROOT_DIR, vm_id,
                                base_config.VM_DEST_DIR, ".ssh/authorized_keys"))

        logger.debug("public key location = %s, authorized key location = %s" %
                    (public_key_file, authorized_key_file))
        command = (r'ssh -o "%s" %s "%s %s > %s"' %
                    (base_config.NO_STRICT_CHECKING,
                    base_config.BASE_IP_ADDRESS,
                    "/bin/cat", public_key_file, authorized_key_file))
        logger.debug("command to cpy the public key = %s" % command)
        (ret_code,output) = execute_command(command)
        return True
    except Exception, e:
        logger.error("ERROR = %s" % str(e))
        return False


def copy_files(src_dir, dest_dir):

    try:
        copy_command = "rsync -arz --progress " + src_dir + " " + dest_dir
        logger.debug("copy command = %s" % copy_command)
        command = (r'ssh -o "%s" %s "%s"' %
                   (base_config.NO_STRICT_CHECKING,
                    base_config.BASE_IP_ADDRESS, copy_command))
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


def copy_ovpl_source(vm_id):
    
    src_dir =  "%s%s%s" % (base_config.VM_ROOT_DIR, base_config.ADS_SERVER_VM_ID,
                           base_adapter.OVPL_DIR_PATH)
    dest_dir = "%s%s%s" % (base_config.VM_ROOT_DIR, vm_id, base_config.VM_DEST_DIR)
    logger.debug("vm_id = %s, src_dir=%s, dest_dir=%s" % (vm_id, src_dir, dest_dir))

    try:
        return copy_files(str(src_dir), str(dest_dir))
    except Exception, e:
        logger.error("ERROR = %s" % str(e))
        return False

def copy_lab_source(vm_id, lab_repo_name, git_clone_loc):

    directories = git_clone_loc.split("/")
    labs_dir = directories[-2]
    src_dir =  "%s%s%s%s%s%s" % (base_config.VM_ROOT_DIR,
                                 base_config.ADS_SERVER_VM_ID,
                                 base_config.VM_DEST_DIR, labs_dir,
                                 "/", lab_repo_name)

    dest_dir = "%s%s%s" % (base_config.VM_ROOT_DIR, vm_id,
                           base_config.VM_DEST_DIR + "labs")

    logger.debug("vm_id = %s, src_dir=%s, dest_dir=%s" %
                 (vm_id, src_dir, dest_dir))

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
    lab_ID = get_test_lab_id() if vm_spec["lab_ID"] == "" else vm_spec["lab_ID"]
    host_name = lab_ID + "." + base_adapter.get_adapter_hostname()
    os_template = find_os_template(vm_spec["os"], vm_spec["os_version"])
    (ram, swap) = vm_utils.get_ram_swap(vm_spec["ram"], vm_spec["swap"])
    (disk_soft, disk_hard) = vm_utils.get_disk_space(vm_spec["diskspace"])
    vm_create_args = " --ostemplate " + os_template + \
                     " --diskspace " + disk_soft + ":" + disk_hard + \
                     " --hostname " + host_name
    # Note to self: check ram format "0:256M" vs "256M"
    vm_set_args = " --netif_add eth0,,,," + config.SUBNET_BRIDGE + \
                  " --ram " + ram + \
                  " --swap " + swap + \
                  " --nameserver " + base_config.ADAPTER_NAME_SERVER + \
                  " --onboot yes" + \
                  " --save"

    return (vm_create_args, vm_set_args)


def find_os_template(os, os_version):
    """
    Find a suitable os template from the list of supported templates from
    the given OS and OS version. If a suitable OS is not found, raise
    appropriate Exception
    """
    logger.debug("OS = %s and OS_VERSION = %s" % (os, os_version))
    supported_template = config.supported_template
    logger.debug("Supported template = %s" % supported_template)

    if os == "" or os_version == "":
        msg = "No OS or Version specified"
        logger.error(msg)
        raise OSNotFound(msg)

    # sanitize input
    os = os.strip().upper()
    os_version = os_version.strip()

    if os == 'UBUNTU' and os_version == '12':
        os_version = '12.04'

    if os == 'UBUNTU' and os_version == '13':
        os_version = '13.04'

    # filter the supported template list by the os and the by the version
    all_versions_of_os = filter(lambda x: x['os'] == os, supported_template)
    logger.debug("List of all the supported versions of OS = %s is %s" %
                 (os, all_versions_of_os))

    if all_versions_of_os:
        chosen_template = filter(lambda x: x['version'] ==
                                 os_version, all_versions_of_os)
        logger.debug("The templete supported for OS = %s, Version = %s is %s" %
                     (os, os_version, chosen_template))
    else:
        msg = "OS = %s is not supported" % os
        logger.error(msg)
        raise OSNotFound(msg)

    if not chosen_template or not len(chosen_template):
        msg = "Version = %s is not supported" % os_version
        logger.error(msg)
        raise OSNotFound(msg)

    # chose the item; there should be only one.
    chosen_template = chosen_template[0]

    logger.debug("Choosen Template: %s; based on input OS: %s, version: %s" %
                 (chosen_template, os, os_version))
    return chosen_template['template']


def validate_vm_id(vm_id):
    vm_id = str(vm_id).strip()
    m = re.match(r'^([0-9]+)$', vm_id)
    if m == None:
        raise InvalidVMIDException("Invalid VM ID.  VM ID must be numeric.")
    vm_id = int(m.group(0))
    if vm_id <= 0:
        raise InvalidVMIDException("Invalid VM ID.  VM ID must be greater than 0.")
    if vm_id > base_config.MAX_VM_ID:
        raise InvalidVMIDException("Invalid VM ID.  Specify a smaller VM ID.")
    return str(vm_id)

def create_vm_id(vm_id):
    """If no vm_id is specified, it is computed using the last two segments"""
    """of an available IP address; vm_spec is an object """
    logger.debug("create_vm_id(): vm_id = %s" % vm_id)
    if vm_id == "":
        global IP_ADDRESS
        IP_ADDRESS = base_adapter.find_available_ip()
        m = re.match(r'[0-9]+.[0-9]+.([0-9]+).([0-9]+)', IP_ADDRESS)
        if m != None:
            vm_id = str((int(m.group(1) + m.group(2))))
        else:
            vm_id = validate_vm_id(vm_id)
    logger.debug("create_vm_id(): vm_id = %s" % vm_id)
    return vm_id

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


if __name__ == "__main__":

    # Start an HTTP server and wait for invocation
    # Parse the invocation command and route to
    # appropriate methods.
    #test()
    if copy_ovpl_source(584):
        logger.debug("test Successful")
    else:
        logger.debug("test UNSuccessful")
