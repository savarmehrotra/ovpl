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
    'migrate_vm',
    'get_resource_utilization',
    'take_snapshot',
    'InvalidVMIDException',
]

# Standard Library imports
import os
import json
#import sys
import socket
from time import sleep

# Third party imports
# aws library
from boto import ec2

# VLEAD imports
import VMUtils
from dict2default import dict2default
import settings
import BaseAdapter
from http_logging.http_logger import logger
from utils.git_commands import *
from utils.envsetup import EnvSetUp
from utils.execute_commands import *

# import the AWS configuration
import aws_config as config

#GIT_CLONE_LOC = "labs"


class AMINotFound(Exception):
    pass

class AWSKeyFileNotFound(Exception):
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

    def __init__(self):
        # check if the key_file exists, else throw an error! again the key file
        # should not be checked in, but the deployer has to manually copy it in
        # this location
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        key_file_path = os.path.join(cur_dir, self.key_name+'.pem')
        # logger.debug("Key file path: %s", key_file_path)
        if not os.path.isfile(key_file_path):
            msg = 'Make sure you have the key file: "%s.pem" ' % self.key_name
            msg += ' placed in the same directory as the adapter file'
            raise AWSKeyFileNotFound(msg)

        self.connection = self.create_connection()

    def create_connection(self):
        return ec2.connect_to_region(self.region, **self.credentials)

    def create_vm(self, lab_spec, dry_run=False):
        logger.debug("AWSAdapter: create_vm()")

        # (vm_create_args, vm_set_args) = construct_vzctl_args(lab_spec)
        (ami_id, instance_type) = construct_ec2_args(lab_spec)

        logger.debug("AWSAdapter: creating VM with following params:\
                     instance_type: %s, AMI id: %s" % (instance_type, ami_id))

        reservation = self.connection.\
            run_instances(ami_id,
                          key_name=self.key_name,
                          instance_type=instance_type,
                          subnet_id=self.subnet_id,
                          security_group_ids=self.security_group_ids,
                          dry_run=dry_run)

        instance = reservation.instances[0]
        instance.add_tag('Name', 'test.aws.adapter')

        logger.debug("AWSAdapter: created VM: %s" % instance)
        return instance.id

    def init_vm(self, vm_id, lab_repo_name):
        vm_ip_addr = self.get_vm_ip(vm_id)

        logger.debug("ip add of instance id %s is %s" % (vm_id, vm_ip_addr))

        ## FIXME: remove the following
        line1 = "Host {0}".format(vm_ip_addr)
        line2 = "ProxyCommand /usr/bin/corkscrew proxy.vlabs.ac.in 8080 %h %p ~/.proxy_auth"
        command = "echo \"%s\" >> /home/ecthiender/.ssh/config" % line1.strip()
        execute_command(command)
        command = "echo \"%s\" >> /home/ecthiender/.ssh/config" % line2.strip()
        execute_command(command)

        logger.debug("AWSAdapter: init_vm(): vm_id = %s" % vm_id)

        while not self.is_running_vm(vm_ip_addr):
            print "waiting for SSH to be up..."
            sleep(3)

        #success = init_copy_files(vm_ip_addr)
        #if not success:
        #    return False

        success = copy_ovpl_source(vm_ip_addr)
        if not success:
            return False

        success = copy_lab_source(vm_ip_addr, lab_repo_name)
        if not success:
            return False

        success = self.start_vm_manager(vm_id)
        if not success:
            return False

        # Return the VM's IP and port info
        response = {"vm_id": vm_id, "vm_ip": vm_ip_addr,
                    "vmm_port": settings.VM_MANAGER_PORT}
        logger.debug("AWSAdapter: init_vm(): success = %s, response = %s" % (success, response))

        return (success, response)

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
        stopped_instances = self.stop_vm(vm_id, dry_run=dry_run)
        started_instances = self.start_vm(vm_id, dry_run=dry_run)
        return started_instances

    def start_vm_manager(self, vm_id):
        return None
        command = VZCTL + " exec " + str(vm_id) + " \"su - root -c \'python " + \
            settings.VMMANAGERSERVER_PATH + settings.VM_MANAGER_SCRIPT + " &\'\""
        logger.debug("CentOSVZAdapter: start_vm_manager(): command = %s" % command)
        try:
            execute_command(command)
            return True
        except Exception, e:
            logger.error("CentOSVZAdapter: start_vm_manager(): command = %s, ERROR = %s" % (command, str(e)))
            return False

    # take an aws instance_id and return its ip address
    def get_vm_ip(self, vm_id):
        logger.debug("AWSAdapter: get_vm_ip(%s)" % (vm_id))

        # FIXME: remove it when running ADS from AWS cluster
        # sometimes if this function is called immediately after creating the VM
        # the VM does not get a public ip address assigned to it.
        # so a HACK for now to wait until it gets a public ip
        while True:
            reservations = self.connection.get_all_instances(instance_ids=[vm_id])
            instance = reservations[0].instances[0]
            logger.debug("AWSAdapter: instance: %s with id: %s" %
                        (instance.__dict__, vm_id))

            if instance.ip_address is not None:
                break
            logger.debug("AWSAdapter: IP address of instance is %s"
                         % instance.ip_address)
            logger.debug("AWSAdapter: waiting for the VM to be up..")
            sleep(5)

        logger.debug("AWSAdapter: got ip addr: %s" % (instance.ip_address))
        return instance.ip_address

    def get_resource_utilization(self):
        pass

    def test_logging(self):
        logger.debug("AWSAdapter: test_logging()")
        pass

    # check if the VM is up and port 22 is reachable
    # assumption is VM is running the SSH service
    def is_running_vm(self, vm_ip):
        #vm_id = validate_vm_id(vm_id)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((vm_ip, 22))
            print "VM: Port 22 reachable"
            return True
        except socket.error as e:
            print "VM: Error on connect: %s" % e
            s.close()
            return False

    def migrate_vm(self, vm_id, destination):
        #vm_id = validate_vm_id(vm_id)
        pass

    def take_snapshot(self, vm_id):
        #vm_id = validate_vm_id(vm_id)
        pass


# FIXME: change this root; when we get the AMI to have root login fixed.
VM_USER = 'ubuntu'

def init_copy_files(ip_addr):
    # Before rsync can be used to copy files or before running commands on
    # instance using SSH we should add key-pair and accept SSH fingerprint
    # NOTE that accepting SSH fingerprint in this manner is susceptible to
    # MITM attacks.
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    key_file_path = os.path.join(cur_dir, config.key_file_name+'.pem')

    try:
        execute_command("ssh-add {0}".format(key_file_path))
    except Exception, e:
        logger.debug("Error adding key-pair to VM: %s" % str(e))
        return False

    try:
        execute_command("ssh -o StrictHostKeyChecking=no ubuntu@{0} 'ls'".\
                        format(ip_addr))
    except Exception, e:
        logger.debug("Error accepting SSH fingerprint of VM: %s" % str(e))
        return False

    return True


def copy_files(src_dir, dest_dir):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    key_file_path = os.path.join(cur_dir, config.key_file_name+'.pem')

    try:
        command = "scp -i {0} -r -o StrictHostKeyChecking=no {1} {2}".\
            format(key_file_path, src_dir, dest_dir)

        #command = "rsync -varz --progress {0} {1}".format(src_dir, dest_dir)

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
    src_dir = env.get_ovpl_directory_path()
    #FIXME: change the following /home/VM_USER to settings.VM_DEST_DIR
    dest_dir = "{0}@{1}:{2}ovpl/".format(VM_USER, ip_addr, "/home/"+VM_USER+"/")

    logger.debug("ip_address = %s, src_dir=%s, dest_dir=%s" %
                 (ip_addr, src_dir, dest_dir))

    try:
        return copy_files(src_dir, dest_dir)
    except Exception, e:
        logger.error("ERROR = %s" % str(e))
        print 'ERROR= %s' % (str(e))
        return False


def copy_lab_source(ip_addr, lab_repo_name):
    src_dir = GIT_CLONE_LOC[:-1] + "/" + lab_repo_name
    #FIXME: change the following /home/VM_USER to settings.VM_DEST_DIR
    dest_dir = "{0}@{1}:{2}labs/".format(VM_USER, ip_addr, "/home/"+VM_USER+"/")

    logger.debug("ip_address = %s, src_dir=%s, dest_dir=%s" % (ip_addr, src_dir, dest_dir))

    try:
        return copy_files(src_dir, dest_dir)
    except Exception, e:
        logger.error("ERROR = %s" % str(e))
        print 'ERROR= %s' % (str(e))
        return False


def get_vm_spec(lab_spec):
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


def construct_ec2_args(lab_spec):
    """
    Returns a tuple of aws vm arguments - AMI id and instance type based
    on the lab_spec parameters
    """
    available_instance_types = [
        {'ram': 1024, 'instance_type': 't2.micro'},
        {'ram': 2048, 'instance_type': 't2.small'}
        #{'ram': 4096, 'instance_type': 't2.micro'}
    ]

    vm_spec = get_vm_spec(lab_spec)

    if 'slug' in lab_spec['lab']['description']:
        hostname = "%s.%s" % (slug, settings.get_adapter_hostname())
    else:
        if vm_spec["lab_ID"] == "":
            lab_ID = settings.get_test_lab_id()
        else:
            lab_ID = vm_spec["lab_ID"]
        hostname = "%s.%s" % (lab_ID, settings.get_adapter_hostname())

    ami_id = find_ec2_ami(vm_spec["os"], vm_spec["os_version"])

    (ram, swap) = VMUtils.get_ram_swap(vm_spec["ram"], vm_spec["swap"])

    # convert stupid RAM string in 'M' to an integer
    ram = int(ram[:-1])
    if ram < 2048:
        instance_type = available_instance_types[0]['instance_type']
    else:
        instance_type = available_instance_types[1]['instance_type']

    #(disk_soft, disk_hard) = VMUtils.get_disk_space(vm_spec["diskspace"])
    #print disk_soft, disk_hard

    return (ami_id, instance_type)


def find_ec2_ami(os, os_version):
    """
    Find a suitable AMI from the list of supported AMIs from the given OS and
    OS version. If not a suitable OS is found, raise appropriate Exception
    """
    supported_amis = [
        #{'os': 'UBUNTU', 'version': '12.04', 'ami_id': 'ami-5ca18834'},
        {'os': 'UBUNTU', 'version': '12.04', 'ami_id': 'ami-58b49c30'},
        {'os': 'UBUNTU', 'version': '14.04', 'ami_id': 'ami-9a562df2'},
        {'os': 'CENTOS', 'version': '6.6', 'ami_id': 'ami-61655b08'},
        {'os': 'DEBIAN', 'version': '7.0', 'ami_id': 'ami-e0efab88'}
    ]

    if os == "" or os_version == "":
        raise AMINotFound('No corresponding AMI for the given OS found')

    # sanitize input
    os = os.strip().upper()
    os_version = os_version.strip()

    if os == 'UBUNTU' and os_version == '12':
        os_version = '12.04'

    # filter the supported_amis list by the os and the by the version
    filtered_os = filter(lambda x: x['os'] == os, supported_amis)
    chosen_ami = filter(lambda x: x['version'] == os_version, filtered_os)

    if not chosen_ami or not len(chosen_ami):
        raise AMINotFound('No corresponding AMI for the given OS found')

    # chose the item; there should be only one.
    chosen_ami = chosen_ami[0]

    print chosen_ami
    return chosen_ami['ami_id']


if __name__ == "__main__":

    #find_ec2_ami('cent OS', '6.5')
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
    #obj.get_vm_ip('i-5e8622a2')
    #obj.destroy_vm(instance_id)
