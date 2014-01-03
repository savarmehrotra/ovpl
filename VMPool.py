# Author: Chandan Gupta
# Contact: chandan@vlabs.ac.in

""" VMPool module description 

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
case of POST or PUT request, the request data should be in Python dictionary. 
The requests module will handle converting it to proper POST/PUT url format

Example usage: 

>>>import requests
>>>response_object = requests.get(url='http://www.google.com')
>>>print response_object.status_code

>>>payload = {'username': 'avinash', 'password': 'avinash'}
>>>response_object_post = requests.post(url='http://www.google.com/login', 
                                        data=payload)

>>>response_object_put = requests.put(url='http://www.google.com/login', 
                                        data=payload)

>>>response_object_delete = requests.delete(url='http://google.com/accounts')
>>>print response_object_delete.text
"""

__all__ = [
    'VMProxy',
    'VMPool',
    ]

import VMSpec

class VMProxy:
    """ The proxy object corresponding to a VM """

    def __init__(self, VM_ID, ip_address, port):
        self.VM_ID = VM_ID.strip()
        self.ip_address = ip_address.strip()
        self.port = port.strip()


class VMPool:
    """ Manages a pool of VMs or VMProxy's """

    def __init__(self, adapter_ip, adapter_port):
        self.VMs = []
        self.adapter_ip = adapter_ip
        self.adapter_port = adapter_port

    def create_VM(self, VM_spec):
        # Allocate a VM_ID
        # Invoke platform adapter
        # Construct VMProxy
        # Add to VMs list
        pass

    def destroy_VM(self, VM_ID):
        # Invoke platform adapter
        # Delete entry from VMs list
        pass
