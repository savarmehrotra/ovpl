"""
VMPoolManager manages a set of VMPools i.e.
maintain a list of available VMPools
and decide which VMPool to use for creating a VM.
"""
from __init__ import *
from vm_pool import VMPool
from state import State
from httplogging.http_logger import logger
from utils.envsetup import EnvSetUp


class RecordNotFoundError(Exception):
    def __init__(self, lab_id):
        self.lab_id = lab_id

    def __str__(self):
        return repr(self.lab_id)


class VMPoolManager:
    state = None
    VMPools = None
    env = None
    config_spec = None
    create_url = None
    destroy_url = None

    def __init__(self):
        """ State should be rewriten"""
        logger.debug("VMPoolManager: _init_()")
        self.state = State.Instance()
        self.vmPools = []
        self.env = EnvSetUp.Instance()
        self.config_spec = self.env.get_config_spec()
        self.pools = self.config_spec["VMPOOL_CONFIGURATION"]["VMPOOLS"]
        self.create_uri = self.config_spec["API_ENDPOINTS"]["CREATE_URI_ADAPTER_ENDPOINT"]
        self.destroy_uri = self.config_spec["API_ENDPOINTS"]["DESTROY_URI_ADAPTER_ENDPOINT"]

        for pool in self.pools:
            self.add_vm_pool(pool["POOLID"],
                             pool["DESCRIPTION"],
                             pool["ADAPTERIP"],
                             pool["PORT"],
                             self.create_uri,
                             self.destroy_uri)
        logger.debug("VMPoolManager: _init_();  vm_pools = %s" % (str(self.vmPools)))

    def add_vm_pool(self, vm_pool_id, vm_description, adapter_ip,
                    adapter_port, create_path, destroy_path):
        logger.debug("VMPoolManager: add_vm_pool(); %s, %s, %s, %s, %s, %s" %
                     (vm_pool_id, vm_description, adapter_ip,
                      adapter_port, create_path, destroy_path))
        self.vmPools.append(VMPool(vm_pool_id, vm_description,
                            adapter_ip, adapter_port,
                            create_path, destroy_path))

    def get_available_pool(self, lab_spec):
        """Imagining four VMPools:
        0. For Linux VMs in private data center (uses OpenVZ)
        1. For Amazon S3 (static content hosting)
        2. For Windows VMs in private data center (uses KVM)
        3. For Amazon EC2

        """
        logger.debug("VMPoolManager: get_available_pool()")
        if self.is_lab_static(lab_spec):
            return self.VMPools[1]
        elif self.is_lab_on_windows(lab_spec):
            return self.VMPools[2]
        else:
            return self.VMPools[0]

    def is_lab_static(self, lab_spec):
        return False

    def is_lab_on_windows(self, lab_spec):
        return False

    def create_vm(self, lab_spec):
        logger.debug("VMPoolManager: create_vm()")
        vmpool = self.get_available_pool(lab_spec)
        return vmpool.create_vm(lab_spec)

    def undeploy_lab(self, lab_id):
        logger.debug("VMPoolManager: undeploy_lab()")
        used_pools = self.get_used_pools(lab_id)
        for pool_id in used_pools:
            self.VMPools[pool_id].undeploy_lab(lab_id)

    def get_used_pools(self, lab_id):
        used_pools = []
        logger.debug("VMPoolManager: get_used_pools()")
        deployment_record = self.state.get_record(lab_id)
        logger.debug("Deployment Record = %s" % deployment_record)
        if deployment_record is not None:
            # Currently there is only pool where the lab is deployed
            used_pools.append(deployment_record['vmpool_info']['vmpool_id'])
            return used_pools
        else:
            logger.error("No record found with the lab id = %s" % lab_id)
            raise RecordNotFoundError(lab_id)


if __name__ == '__main__':
    vmPoolMgr = VMPoolManager()
    used_pools = None
    try:
        used_pools = vmPoolMgr.get_used_pools('cse044')
    except Exception, e:
        logger.debug("No record found with lab_id = %s" % e.lab_id)

    print used_pools
