"""
VMPool manages a pool of VMs and the resources available for use by the VMs.
Resources may include RAM, diskspace, IPs, etc.  For now, these resources
are handled by the platform adapters.  VMPool does this by maintaining a
list of VMs via corresponding VMProxy objects.

"""

__all__ = [
    'VMProxy',
    'VMPool',
    ]

import json
import requests
from exceptions import Exception
from __init__ import *
from httplogging.http_logger import logger
from state import Record


class VMPool:
    """ Manages a pool of VMs or VMProxy's """

    vmpool_id = None
    vm_description = None
    adapter_ip = None
    adapter_port = None
    create_path = None
    destroy_path = None

    def __init__(self, vmpool_id, vm_description, adapter_ip, adapter_port,
                 create_path, destroy_path):

        logger.debug("VMPool: __init__(); poolID=%s, Desciption=%s"
                     "AdapterIP=%s, AdapterPort=%s, CreatePath=%s"
                     "DestroyPath=%s" % (vmpool_id, vm_description,
                                         adapter_ip, adapter_port,
                                         create_path, destroy_path))

        # self.vms = []       # List of VMProxy objects
        self.vmpool_id = vmpool_id
        self.vm_description = vm_description
        self.adapter_ip = adapter_ip
        self.adapter_port = adapter_port
        self.create_path = create_path
        self.destroy_path = destroy_path

    def construct_state(self, lab_spec, vm_id, vm_ip, vm_port):
        deploy_record = Record().record
        logger.debug("before setting record = %s" % deploy_record)
        deploy_record["lab_spec"] = lab_spec
        deploy_record["vm_info"]["vm_id"] = vm_id
        deploy_record["vm_info"]["vm_ip"] = vm_ip
        deploy_record["vm_info"]["vm_port"] = vm_port
        deploy_record["vmpool_info"]["vmpool_id"] = self.vmpool_id
        deploy_record["vmpool_info"]["vm_description"] = self.vm_description
        deploy_record["vmpool_info"]["adapter_ip"] = self.adapter_ip
        deploy_record["vmpool_info"]["adapter_port"] = self.adapter_port
        return deploy_record

    def create_vm(self, lab_spec):
        # vm_spec is a json string
        # Allocate a vm_id: not required as platform adapter will allocate it.
        # Invoke platform adapter server (POST)

        logger.debug("VMPool: create_vm(); poolID=%s, Desciption=%s"
                     "AdapterIP=%s, AdapterPort=%s, CreatePath=%s"
                     "DestroyPath=%s" % (self.vmpool_id, self.vm_description,
                                         self.adapter_ip, self.adapter_port,
                                         self.create_path, self.destroy_path))

        adapter_url = "%s:%s%s" % (self.adapter_ip, self.adapter_port,
                                   self.create_path)
        payload = {'lab_spec': json.dumps(lab_spec)}

        logger.debug("VMPool: create_vm(); adapter_url = %s, payload = %s" %
                     (adapter_url, str(payload)))

        try:
            result = requests.post(url=adapter_url, data=payload)
            logger.debug("VMPool: create_vm(): Response text from adapter: " +
                         result.text)
            if result.status_code == requests.codes.ok:
                vm_id = result.json()["vm_id"]
                vm_ip = result.json()["vm_ip"]
                vm_port = result.json()["vmm_port"]
                return construct_state(lab_spec, vm_id, vm_ip, vm_port)
            else:
                raise Exception("VMPool: create_vm(): Error creating VM: " +
                                result.text)
        except Exception, e:
            logger.error("VMPool: create_vm(): Error communicating with" +
                         "adapter: " + str(e))
            raise Exception("VMPool: create_vm(): Error creating VM: " +
                            str(e))

    def destroy_vm(self, vm_id):
        # Invoke platform adapter
        # Delete entry from VMs list
        logger.debug("VMPool.destroy_vm()")
        adapter_url = "%s:%s:%s" % (self.adapter_ip, self.adapter_port,
                                    self.destrpy_path)
        payload = {'vm_id': vm_id}
        try:
            result = requests.post(url=adapter_url, data=payload)
            logger.debug("Response text from adapter: " + result.text)
            if (result.status_code == requests.codes.ok and
               "Success" in result.text):
                logger.debug("VMPool.destroy_vm()")
                return True
            else:
                logger.error("Error destroying vm: " + result.text)
        except Exception, e:
            logger.error("Error communicating with adapter: " + str(e))

if __name__ == "__main__":
    # pool = VMPool("http://10.4.12.24", "8000")
    # pool.create_vm(None)
    def test_construct_state():
        vmpool_id = 1
        vm_description = "LINUXAdapter"
        adapter_ip = "http://localhost"
        adapter_port = "8000"
        create_path = "/api/1.0/vm/create"
        destroy_path = "/api/1.0/vm/destroy"

        vm_pool = VMPool(vmpool_id, vm_description, adapter_ip,
                         adapter_port, create_path, destroy_path)
        lab_spec = "Hello World"
        vm_id = "123"
        vm_ip = "10.12.13.114"
        vm_port = "8089"
        deploy_record = vm_pool.construct_state(lab_spec, vm_id,
                                                vm_ip, vm_port)
        logger.debug("test_construct_state: record = %s" % deploy_record)

    test_construct_state()
