# Author: Chandan Gupta
# Contact: chandan@vlabs.ac.in

""" VMPool manages a pool of VMs and the resources available for use by the VMs.
    Resources may include RAM, diskspace, IPs, etc.  For now, these resources 
    are handled by the platform adapters.  VMPool does this by maintaining a
    list of VMs via corresponding VMProxy objects.
"""

__all__ = [
    'VMProxy',
    'VMPool',
    ]

import VMSpec

#Globals
CREATE_PATH = "/api/1.0/create"

class VMProxy:
    """ The proxy object corresponding to a VM """

    def __init__(self, vm_id, ip_address, port):
        self.vm_id = vm_id.strip()
        self.ip_address = ip_address.strip()
        self.port = port.strip()


class VMPool:
    """ Manages a pool of VMs or VMProxy's """

    def __init__(self, adapter_ip, adapter_port):
        self.vms = []       # List of VMProxy objects
        self.adapter_ip = adapter_ip
        self.adapter_port = adapter_port

    def create_vm(self, vm_spec):
        # vm_spec is a json string
        # Allocate a vm_id: not required as platform adapter will allocate it.
        # Invoke platform adapter server
        my_request = HTTPClientRequest(vm_spec, self.adapter_ip, 
                                       self.adapter_port, CREATE_PATH, "POST")
        response = my_request.execute()
        # Extract vm_id, ip_address and port from response
        pass
        # Construct VMProxy and add to VMs list
        self.vms.append(VMProxy(vm_id, ip_address, port))

    def destroy_vm(self, vm_id):
        # Invoke platform adapter
        # Delete entry from VMs list
        pass
