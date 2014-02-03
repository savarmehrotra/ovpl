
"""
VMPoolManager manages a set of VMPools i.e. maintain a list of available VMPools
and decide which VMPool to use for creating a VM.
"""

import VMPool
from OVPLLogging import *

class VMPoolManager:
    def __init__(self):
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
        OVPL_LOGGER.debug("VMPoolManager.create_vm()")
        vmpool = self.get_available_pool(lab_spec)
        return vmpool.create_vm(lab_spec)
