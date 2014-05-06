#!/bin/python

# Author : Avinash <a@vlabs.ac.in>
# Organization : VLEAD, Virtual-Labs

# Services exposed by CentOSVZAdapter
# http://host-name/api/1.0/vm/create

import json
import urlparse
import urllib

import tornado.httpserver 
import tornado.ioloop 
import tornado.options 
import tornado.web
from tornado.options import define, options

import CentOSVZAdapter


define("port", default=8000, help="run on the given port", type=int)


class CreateVMHandler(tornado.web.RequestHandler):
    def get(self):
        pass

    def post(self):
        post_data = dict(urlparse.parse_qsl(self.request.body))
        result = CentOSVZAdapter.create_vm(json.loads(post_data['lab_spec']))
        self.write(result)
        

class DestroyVMHandler(tornado.web.RequestHandler):
    def get(self):
        pass

    def post(self):
        post_data = dict(urlparse.parse_qsl(self.request.body))
        result = CentOSVZAdapter.destroy_vm(post_data['vm_id'])
        self.write(result)


class RestartVMHandler(tornado.web.RequestHandler):
    def get(self):
        pass

    def post(self):
        pass    


if __name__ == "__main__": 
    tornado.options.parse_command_line()
    config_spec = json.loads(open("../config/config.json").read())
    options.port = config_spec["ADAPTER_CONFIG"]["SERVER_PORT"]    
    app = tornado.web.Application(
        handlers=[
            (config_spec["ADAPTER_CONFIG"]["CREATE_URI"], CreateVMHandler),
            (config_spec["ADAPTER_CONFIG"]["DESTROY_URI"], DestroyVMHandler),
            (config_spec["ADAPTER_CONFIG"]["RESTART_URI"], RestartVMHandler)
        ],
        debug = True)
    http_server = tornado.httpserver.HTTPServer(app) 
    http_server.listen(options.port) 
    tornado.ioloop.IOLoop.instance().start()
