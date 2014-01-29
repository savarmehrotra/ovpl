
"""
VMPoolManager manages a set of VMPools i.e. maintain a list of available VMPools
and decide which VMPool to use for creating a VM.
"""

import VMPool

class VMPoolManager:
    def __init__(self):
        self.VMPools = []

    def add_vm_pool(self, adapter_ip, adapter_port):
        self.VMPools.append(VMPool.VMPool(adapter_ip, adapter_port))

    def get_available_pool(self, vm_spec):
        return self.VMPools[0]

    def create_vm(self, vm_spec):
        vmpool = self.get_available_pool(vm_spec)
        return vmpool.create_vm(vm_spec)