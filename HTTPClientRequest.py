""" 
This creates an HTTPClientRequest object. The constructor receives the JSON 
file which contains the request. Then it creates the object with the data
specified from the JSON, builds the appropriate GET/POST URL. When Execute 
method is called, the request is sent to server
"""

import urllib2
import sys
import os
import re
import json
from urllib import urlencode


class HTTPClientRequest(object):
    """docstring for HTTPClientRequest"""

    def __init__(self, request_specs, host_name, port_number, request_url_path, request_type=None):
        """ Initializes the object """    
        self.base_url = self._set_base_url(host_name, port_number, request_url_path)
        self.create(request_specs)

    def create(self, request_specs):
        """ Creates the request """
        try:
            payload = self._convert_json_to_dict(request_specs)
            payload = self._encode_payload(payload)
            self.request_url = urllib2.Request(url=self.base_url, data=payload)
        except Exception, e:
            raise e 

    def execute(self):
        """ Executes the request and returns the response object """
        try:
            return urllib2.urlopen(self.request_url)
        except urllib2.URLError, e:
            raise e
        except urllib2.HTTPError, e:
            raise e 

    def _convert_json_to_dict(self, request_specs):
        """ Converts the JSON into dictionary """
        return json.loads(request_specs)

    def _encode_payload(self, payload):
        """ Returns the string of enocoded url into proper POST url format """
        return urlencode(payload)    

    def _set_base_url(self, host_name, port_number, request_url_path):
        """ Returns the string in the hostname:port format """
        return "%s:%s/%s" % (host_name, port_number, request_url_path)