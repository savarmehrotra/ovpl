#!/bin/python

# Author : Avinash <a@vlabs.ac.in>
# Organization : VLEAD, Virtual-Labs

# Services exposed by CentOSVZAdapter
# http://host-name/api/1.0/vm/create

import json
import urlparse
import urllib
import os.path

import tornado.httpserver 
import tornado.ioloop 
import tornado.options 
import tornado.web
from tornado.options import define, options

import CentOSVZAdapter
from CentOSVZAdapter import CENTOSVZ_LOGGER

define("port", default=8000, help="run on the given port", type=int)


class CreateVMHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello SIddharth")

    def post(self):
        CENTOSVZ_LOGGER.debug("CentOSVZAdapterServer: post()")
        post_data = dict(urlparse.parse_qsl(self.request.body))
        CENTOSVZ_LOGGER.debug("CentOSVZAdapterServer: post(); post_data = %s" % (str(post_data)))
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

    CentOSVZAdapter.test_logging()
    CENTOSVZ_LOGGER.debug("CentOSVZAdapterServer: __main__()")

    tornado.options.parse_command_line()
    current_file_path = os.path.dirname(os.path.abspath(__file__))
    config_spec = json.loads(open(current_file_path + "/../config/config.json").read())
    options.port = config_spec["ADAPTER_CONFIG"]["ADAPTER_PORT"]
    create_uri = config_spec["ADAPTER_CONFIG"]["CREATE_URI"]
    destroy_uri = config_spec["ADAPTER_CONFIG"]["DESTROY_URI"]
    restart_uri = config_spec["ADAPTER_CONFIG"]["RESTART_URI"]

    CENTOSVZ_LOGGER.debug("CentOSVZAdapterServer: __main__() PORT=%s, CreateURI=%s, DestroyURI=%s, RestartURI=%s" % \
                          (options.port, create_uri, destroy_uri, restart_uri))

    app = tornado.web.Application(
        handlers=[
            (create_uri, CreateVMHandler),
            (destroy_uri, DestroyVMHandler),
            (restart_uri, RestartVMHandler)
        ],
        debug = True)
    http_server = tornado.httpserver.HTTPServer(app) 
    http_server.listen(options.port) 
    tornado.ioloop.IOLoop.instance().start()
