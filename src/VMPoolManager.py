
"""
VMPoolManager manages a set of VMPools i.e. maintain a list of available VMPools
and decide which VMPool to use for creating a VM.
"""

import VMPool
import Logging
from State import State


class VMPoolManager:
    def __init__(self):
        self.system = State.Instance()
        # Work on finishing the below later (may be a separate mongodb document)
        self.VMPools = []
        self.add_vm_pool("http://localhost", "8000")        # Adapter IP and Port

    def add_vm_pool(self, adapter_ip, adapter_port):
        self.VMPools.append(VMPool.VMPool(adapter_ip, adapter_port))

    def get_available_pool(self, lab_spec):
        """Imagining four VMPools:
        0. For Linux VMs in private data center (uses OpenVZ)
        1. For Amazon S3 (static content hosting)
        2. For Windows VMs in private data center (uses KVM)
        3. For Amazon EC2
        
        """
        if self.is_lab_static(lab_spec):
            return self.VMPools[1]
        elif self.lab_on_windows(lab_spec):
            return self.VMPools[2]
        else:
            return self.VMPools[0]

    def is_lab_static(self, lab_spec):
        return False

    def lab_on_windows(self, lab_spec):
        return False

    def create_vm(self, lab_spec):
        Logging.LOGGER.debug("VMPoolManager.create_vm()")
        vmpool = self.get_available_pool(lab_spec)
        return vmpool.create_vm(lab_spec)

    def undeploy_lab(self, lab_id):
        Logging.LOGGER.debug("VMPoolManager.undeploy_lab()")
        used_pools = self.get_used_pools(lab_id)
        for pool_id in used_pools:
            self.VMPools[pool_id].undeploy_lab(lab_id)

    def get_used_pools(self, lab_id):
        return [d['vmpool_info']['vmpool_id'] for d in self.system.state if d['lab_spec']['lab_id']==lab_id]
