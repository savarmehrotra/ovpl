""" A module for managing VMs on the AWS platform """

""" Open issues with the current version:
    1.
"""

__all__ = [
    'create_vm',
    'start_vm',
    'stop_vm',
    'restart_vm',
    'start_vm_manager',
    'destroy_vm',
    'is_running_vm',
    'get_vm_ip'
]

# Standard Library imports
import os
import json
import socket
from time import sleep

# Third party imports
# AWS library
from boto import ec2

# ADS imports
import VMUtils
from dict2default import dict2default
import settings
from http_logging.http_logger import logger
from utils.envsetup import EnvSetUp
from utils.git_commands import *
from utils.execute_commands import *

# import the AWS configuration
import aws_config as config


class AMINotFound(Exception):
    """
    use this exception class to raise an exception when a suitable AMI is not
    found
    """
    pass


class AWSKeyFileNotFound(Exception):
    """
    use this exception class to raise exceptions when AWS .pem key file is
    not found in the current directory
    """
    pass


class AWSAdapter(object):
    """
    The class representing the AWS Adapter. This adapter is responsible for
    creating and manage VMs and initialize VMs on AWS cloud.
    """

    # set AWS specific parameters. Some of these parameters are sensitive and
    # hence are imported from a config file which is not version controlled.
    region = config.region
    credentials = config.credentials
    subnet_id = config.subnet_id
    security_group_ids = config.security_group_ids
    key_name = config.key_file_name
    vm_name_tag = config.vm_tag

    # the username of the destination VMs; this username will be used to SSH and
    # perform operations on the VM
    VM_USER = 'root'

    def __init__(self):
        # check if the key_file exists, else throw an error! again the key file
        # should not be checked in, but the deployer has to manually copy it in
        # this location
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.key_file_path = os.path.join(cur_dir, self.key_name+'.pem')

        # logger.debug("Key file path: %s", key_file_path)
        if not os.path.isfile(self.key_file_path):
            msg = 'Make sure you have the key file: "%s.pem" ' % self.key_name
            msg += ' placed in the same directory as the adapter file'
            raise AWSKeyFileNotFound(msg)

        self.connection = self.create_connection()

    def create_connection(self):
        return ec2.connect_to_region(self.region, **self.credentials)

    def create_vm(self, lab_spec, dry_run=False):
        logger.debug("AWSAdapter: create_vm()")

        (ami_id, instance_type) = self._construct_ec2_params(lab_spec)

        logger.debug("AWSAdapter: creating VM with following params: " +
                     "instance_type: %s, AMI id: %s" % (instance_type, ami_id))

        reservation = self.connection.\
            run_instances(ami_id,
                          key_name=self.key_name,
                          instance_type=instance_type,
                          subnet_id=self.subnet_id,
                          security_group_ids=self.security_group_ids,
                          dry_run=dry_run)

        instance = reservation.instances[0]

        instance.add_tag('Name', self.vm_name_tag)

        logger.debug("AWSAdapter: created VM: %s" % instance)
        return instance.id

    # initialize the VM by copying relevant ADS component (VM Manager) and the
    # lab sources, and start the VM Manager..
    def init_vm(self, vm_id, lab_repo_name):
        """
        initialize the VM by copying relevant ADS component (VM Manager) and
        the lab sources, and start the VM Manager..
        """
        logger.debug("AWSAdapter: init_vm(): vm_id = %s" % vm_id)

        vm_ip_addr = self.get_vm_ip(vm_id)

        logger.debug("instance id: %s; IP addr: %s" % (vm_id, vm_ip_addr))

        # wait until the VM is up with the SSH service..
        # until then we won't be able to go ahead with later steps..
        while not self.is_running_vm(vm_ip_addr):
            logger.debug("AWSAdapter: VM %s: waiting for SSH to be up..." %
                         vm_ip_addr)
            sleep(4)

        # Return the VM's id, IP and port of VM Mgr
        info = {"vm_id": vm_id, "vm_ip": vm_ip_addr,
                "vmm_port": settings.VM_MANAGER_PORT}

        success = self._copy_ovpl_source(vm_ip_addr)
        if not success:
            return (success, info)

        success = self._copy_lab_source(vm_ip_addr, lab_repo_name)
        if not success:
            return (success, info)

        success = self.start_vm_manager(vm_ip_addr)
        if not success:
            return (success, info)

        logger.debug("AWSAdapter: init_vm(): success = %s, response = %s" %
                     (success, info))

        return (success, info)

    def stop_vm(self, vm_id, dry_run=False):
        logger.debug("AWSAdapter: stop_vm(): vm_id = %s" % vm_id)
        logger.debug("AWSAdapter: stopping VM instance: %s" % vm_id)
        return self.connection.stop_instances([vm_id], dry_run=dry_run)

    def start_vm(self, vm_id, dry_run=False):
        logger.debug("AWSAdapter: start_vm(): vm_id = %s" % vm_id)
        return self.connection.start_instances([vm_id], dry_run=dry_run)

    def destroy_vm(self, vm_id, dry_run=False):
        logger.debug("AWSAdapter: destroy_vm(): vm_id = %s" % vm_id)
        logger.debug("AWSAdapter: terminating VM instance: %s" % vm_id)
        return self.connection.terminate_instances([vm_id], dry_run=dry_run)

    def restart_vm(self, vm_id, dry_run=False):
        logger.debug("AWSAdapter: restart_vm(): vm_id: %s" % vm_id)
        stopped_instances = self.stop_vm(vm_id, dry_run=dry_run)
        logger.debug("AWSAdapter: stopped instances: %s" % stopped_instances)
        started_instances = self.start_vm(vm_id, dry_run=dry_run)
        logger.debug("AWSAdapter: started instances: %s" % started_instances)
        return started_instances

    # start the VM Manager component on the lab VM
    def start_vm_manager(self, vm_ip_addr):
        logger.debug("AWSAdapter: Attempting to start VMMgr: vm_ip:%s"
                     % (vm_ip_addr))

        ssh_command = "ssh -i {0} -o StrictHostKeyChecking=no {1}@{2} ".\
            format(self.key_file_path, self.VM_USER, vm_ip_addr)

        vmmgr_cmd = "'python {0}{1} >> vmmgr.log 2>&1 < /dev/null &'".\
            format(settings.VMMANAGERSERVER_PATH, settings.VM_MANAGER_SCRIPT)

        command = ssh_command + vmmgr_cmd

        logger.debug("AWSAdapter: start_vm_manager(): command = %s" % command)

        try:
            execute_command(command)
        except Exception, e:
            logger.error("AWSAdapter: start_vm_manager(): " +
                         "command = %s, ERROR = %s" % (command, str(e)))
            return False

        return True

    # take an aws instance_id and return its ip address
    def get_vm_ip(self, vm_id):
        logger.debug("AWSAdapter: get_vm_ip(): vm_id: %s" % (vm_id))

        reservations = self.connection.get_all_instances(instance_ids=[vm_id])
        instance = reservations[0].instances[0]

        logger.debug("AWSAdapter: IP address of the instance is: %s" %
                     instance.private_ip_address)

        return instance.private_ip_address

    def get_resource_utilization(self):
        pass

    def test_logging(self):
        logger.debug("AWSAdapter: test_logging()")
        pass

    # check if the VM is up and port 22 is reachable
    # assumption is VM is running the SSH service
    def is_running_vm(self, vm_ip):
        logger.debug("AWSAdapter: is_running_vm(): VM IP: %s" % vm_ip)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            logger.debug("AWSAdapter: trying to connect to port 22 of: %s" %
                         vm_ip)
            s.connect((vm_ip, 22))
            logger.debug("AWSAdapter: VM %s: SSH is up.." % vm_ip)
            return True
        except socket.error as e:
            logger.debug("AWSAdapter: VM %s: Error connecting to SSH: %s" %
                         (vm_ip, e))
            logger.debug("AWSAdapter: retrying to reach port 22..")
            s.close()
            return False

    def migrate_vm(self, vm_id, destination):
        pass

    def take_snapshot(self, vm_id):
        pass

    # copy files using rsync given src and dest dirs
    def _copy_files(self, src_dir, dest_dir):
        cmd = "rsync -azr -e 'ssh -i {0} -o StrictHostKeyChecking=no' {1} {2}".\
            format(self.key_file_path, src_dir, dest_dir)

        logger.debug("Command = %s" % cmd)

        try:
            (ret_code, output) = execute_command(cmd)

            if ret_code == 0:
                logger.debug("Copy successful")
                return True
            else:
                logger.debug("Copy Unsuccessful, return code is %s" %
                             str(ret_code))
                return False
        except Exception, e:
            logger.error("ERROR = %s" % str(e))
            return False

    # copy the ADS source into the newly created lab VM
    def _copy_ovpl_source(self, ip_addr):
        env = EnvSetUp()
        src_dir = env.get_ovpl_directory_path()

        dest_dir = "{0}@{1}:{2}".format(self.VM_USER, ip_addr,
                                        settings.VM_DEST_DIR)

        logger.debug("ip_address = %s, src_dir=%s, dest_dir=%s" %
                     (ip_addr, src_dir, dest_dir))

        try:
            return self._copy_files(src_dir, dest_dir)
        except Exception, e:
            logger.error("ERROR = %s" % str(e))
            print 'ERROR= %s' % (str(e))
            return False

    # copy the lab source into the newly created lab VM
    def _copy_lab_source(self, ip_addr, lab_repo_name):
        src_dir = GIT_CLONE_LOC[:-1] + "/" + lab_repo_name

        dest_dir = "{0}@{1}:{2}labs/".format(self.VM_USER, ip_addr,
                                             settings.VM_DEST_DIR)

        logger.debug("ip_address = %s, src_dir=%s, dest_dir=%s" %
                     (ip_addr, src_dir, dest_dir))

        try:
            return self._copy_files(src_dir, dest_dir)
        except Exception, e:
            logger.error("ERROR = %s" % str(e))
            print 'ERROR= %s' % (str(e))
            return False

    def _construct_ec2_params(self, lab_spec):
        """
        Returns a tuple of AWS VM parameters - the AMI id and the instance type
        based on the runtime parameters in the lab_spec
        """

        # get the availabe instance types from the config
        available_instance_types = config.available_instance_types

        # get the vm specs from the lab spec
        vm_spec = self._get_vm_spec(lab_spec)

        # derive hostname from the slug given in labspec
        if 'slug' in lab_spec['lab']['description']:
            hostname = "%s.%s" % (slug, settings.get_adapter_hostname())
        else:
            if vm_spec["lab_ID"] == "":
                lab_ID = settings.get_test_lab_id()
            else:
                lab_ID = vm_spec["lab_ID"]
            hostname = "%s.%s" % (lab_ID, settings.get_adapter_hostname())

        logger.debug("AWSAdapter: hostname of the lab: %s" % hostname)

        # pass OS and OS version and get a relavant AMI id for the corresponding
        # image
        ami_id = self._find_ec2_ami(vm_spec["os"], vm_spec["os_version"])

        # use someone's super intelligent method to get RAM in megs- in a string
        # with 'M' appended at the end!! </sarcasm>
        (ram, swap) = VMUtils.get_ram_swap(vm_spec["ram"], vm_spec["swap"])

        # convert stupid RAM string in 'M' to an integer
        # no idea why would one deal with RAM values in strings!!
        ram = int(ram[:-1])
        if ram < 2048:
            instance_type = available_instance_types[0]['instance_type']
        else:
            instance_type = available_instance_types[1]['instance_type']

        return (ami_id, instance_type)

    def _get_vm_spec(self, lab_spec):
        """ Parse out VM related requirements from a given lab_spec """

        lab_spec = dict2default(lab_spec)
        runtime_reqs = lab_spec['lab']['runtime_requirements']
        vm_spec = {
            "lab_ID": lab_spec['lab']['description']['id'],
            "os": runtime_reqs['platform']['os'],
            "os_version": runtime_reqs['platform']['osVersion'],
            "ram": runtime_reqs['platform']['memory']['min_required'],
            "diskspace": runtime_reqs['platform']['storage']['min_required'],
            "swap": runtime_reqs['platform']['memory']['swap']
        }
        return vm_spec

    def _find_ec2_ami(self, os, os_version):
        """
        Find a suitable AMI from the list of supported AMIs from the given OS
        and OS version. If not a suitable OS is found, raise appropriate
        Exception
        """
        supported_amis = config.supported_amis

        if os == "" or os_version == "":
            raise AMINotFound('No corresponding AMI for the given OS found')

        # sanitize input
        os = os.strip().upper()
        os_version = os_version.strip()

        if os == 'UBUNTU' and os_version == '12':
            os_version = '12.04'

        if os == 'UBUNTU' and os_version == '14':
            os_version = '14.04'

        # filter the supported_amis list by the os and the by the version
        filtered_os = filter(lambda x: x['os'] == os, supported_amis)
        chosen_ami = filter(lambda x: x['version'] == os_version, filtered_os)

        if not chosen_ami or not len(chosen_ami):
            raise AMINotFound('No corresponding AMI for the given OS found')

        # chose the item; there should be only one.
        chosen_ami = chosen_ami[0]

        logger.debug("Choosing AMI: %s; based on input OS: %s, version: %s" %
                     (chosen_ami, os, os_version))

        return chosen_ami['ami_id']



if __name__ == "__main__":

    f = open('../scripts/labspec.json', 'r')
    lspec = json.loads(f.read())
    obj = AWSAdapter()
    print 'creating instance'
    instance = obj.create_vm(lspec)
    sleep(3)
    print obj.get_vm_ip(instance.id)
    lab_repo_name = 'ovpl'
    resp = obj.init_vm(instance.id, lab_repo_name)
    if not resp:
        print 'Something went wrong'
    else:
        print 'Success'
