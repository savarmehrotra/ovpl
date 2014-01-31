# Author: Chandan Gupta
# Contact: chandan@vlabs.ac.in

""" 
VMPool manages a pool of VMs and the resources available for use by the VMs.
Resources may include RAM, diskspace, IPs, etc.  For now, these resources 
are handled by the platform adapters.  VMPool does this by maintaining a
list of VMs via corresponding VMProxy objects.


Requests, a 3rd-party Python module, is used to make requests to VM Pool and 
the response which is sent back to the caller is Requests' response object. 

The response object supports following:
- response_object.status_code
- response_object.headers
- response_object.url
- response_object.text, provides the response body
- response_object.content, provides binary response content 
- response_object.json(), provides response content in JSON 

The Requests module supports GET, POST, PUT, DELETE and OPTIONS requests. In
case of POST or PUT request, the request data should be a Python dictionary. 
The requests module will handle converting it to proper POST/PUT url format

Example usage: 

>>>import requests
GET
===
>>>response_object = requests.get(url='http://www.google.com')
>>>print response_object.status_code
POST
====
>>>payload = {'username': 'avinash', 'password': 'avinash'}
>>>response_object_post = requests.post(url='http://www.google.com/login', 
                                        data=payload)
PUT
===
>>>response_object_put = requests.put(url='http://www.google.com/login', 
                                        data=payload)
DELETE
======
>>>response_object_delete = requests.delete(url='http://google.com/accounts')
>>>print response_object_delete.text
"""

__all__ = [
    'VMProxy',
    'VMPool',
    ]

import json
import requests

#Globals
CREATE_PATH = "/api/1.0/vm/create"

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

    def create_vm(self, lab_spec):
        # vm_spec is a json string
        # Allocate a vm_id: not required as platform adapter will allocate it.
        # Invoke platform adapter server (POST)
        #vm_spec = json.loads(open("vmspec.json", "r").read())
        print "VMPool.create_vm()"
        adapter_url = "%s:%s%s" % (self.adapter_ip, self.adapter_port, CREATE_PATH)
        #print "VMPool::create_vm()", lab_spec
        payload = {'lab_spec': json.dumps(lab_spec)}
        result = requests.post(url=adapter_url, data=payload)
        print result.text
        if result.status_code == requests.codes.ok:
            self.vms.append(VMProxy(result.json()["vm_id"], 
                                    result.json()["vm_ip"], 
                                    result.json()["vm_port"]))
            return (result.json()["vm_ip"], result.json()["vm_port"])
        else:
            return (None, None)

    def destroy_vm(self, vm_id):
        # Invoke platform adapter
        # Delete entry from VMs list
        pass

if __name__ == "__main__":
    pool = VMPool("http://localhost", "8000")
    pool.create_vm(None)