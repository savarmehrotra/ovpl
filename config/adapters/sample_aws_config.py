# AWS specific configuration
# ** IMPORTANT NOTE: Please do not check in this file. This is machine specific
# config **

# the region which we are going to use
region = "us-east-1"
# Credentials can be left empty if IAM is enabled. ADS itself, while creating a
# new VM will take care of user credentials.
credentials = {
        "aws_access_key_id": "your-access-key",
        "aws_secret_access_key": "your-access-secret"
}
# give then key file path - relative to the src directory
# NOTE: advisable to use absolute paths..
key_file_path = "../key_file_name.pem"
# the subnet id to be used
subnet_id = "subnet-id"
# the security groups ids to be used - a list
security_group_ids = ['security group id1', 'security group id 2']
# the default gateway the VMs would use; if no gateway needs to be set, leave it
# empty..
default_gateway = "<ip-address-of-gateway>"

# Configure here the list of supported AMIs
# Its a list of dictionaries.
# Each dictionary must contain the ami_id, os and version fields describing each
# AMI. More details can also be given like tag names etc.
# NOTE: The following can be used w/o modifications. Leave it as it is.
supported_amis = [
        {'os': 'UBUNTU', 'version': '12.04', 'ami_id': 'ami-9c3b0cf4'}
        # {'os': 'UBUNTU', 'version': '14.04', 'ami_id': 'ami-9a562df2'},
        # {'os': 'CENTOS', 'version': '6.6', 'ami_id': 'ami-61655b08'},
        # {'os': 'DEBIAN', 'version': '7.0', 'ami_id': 'ami-e0efab88'}
]

# Configure here the available/supported instance types
# NOTE: The following can be used w/o modifications. Leave it as it is.
available_instance_types = [
        {'ram': 1024, 'instance_type': 't2.micro'},
        {'ram': 2048, 'instance_type': 't2.small'}
]

# Name of the VMs that you want to tag.
# This name is visible on the AWS console
vm_tag = "test.aws.adapter.ads"

# timeout in secs after which waiting for service should be abandoned
TIMEOUT = 300

