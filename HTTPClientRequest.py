""" 
DEPRECATED.

This script creates a HTTPClientRequest object. The constructor receives the string 
which is in JSON format and contains the request. Then it creates the object 
with the data specified from the string, it takes care of building appropriate GET/POST/PUT/DELETE url. 
When Execute method is called, the request is sent to server. The response which is sent back to the caller
is Requests' response object. Request is a 3rd-party python library. 

The response object supports following:
- response_object.status_code
- response_object.headers
- response_object.url
- response_object.text, provides the response body
- response_object.content, provides binary response content 
- response_object.json(), provides response content in JSON 

The caller can provide type of HTTP request or by default GET is assumed.

Example usage:
>>> myJSON = 

"""

import urllib2
import sys
import os
import re
import json
from urllib import urlencode

import requests

class HTTPClientRequest(object):
    """docstring for HTTPClientRequest"""

    def __init__(self, host_name, port_number, request_url_path='', request_type='GET', request_specs=''):
        self.url = self._set_base_url(host_name, port_number, request_url_path)
        self.request_type = request_type
        self.request_specs = request_specs
        self.request_url_path = request_url_path

    def execute(self):
        if self.request_type == 'POST':
            self.payload = self._convert_json_to_dict(self.request_specs)
            return requests.post(url=self.url, data=payload)
        elif self.request_type == 'PUT':
            self.payload = self._convert_json_to_dict(self.request_specs)
            return requests.put(url=self.url, data=payload)
        elif self.request_type == 'DELETE':
            return requests.delete(url=self.url)
        else:
            print 'here'
            print self.base_url
            return requests.get(url=self.url)

    def _convert_json_to_dict(self, request_specs):
        """ Converts the JSON into dictionary """
        return json.loads(request_specs)

    def _set_base_url(self, host_name, port_number, request_url_path):
        """ Returns the string in the hostname:port format """
        return "%s:%s/%s" % (host_name, port_number, request_url_path)

if __name__ == '__main__':
    test = "{'test' : 'hi', 'test1' : 'hello'}"
    responsed = HTTPClientRequest('http://google.com', 80, 'login', request_type='POST', request_specs=test)
    responsed = responsed.execute()
    print responsed.text
    print responsed.url