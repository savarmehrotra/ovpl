#!/bin/python

# Author : Avinash <a@vlabs.ac.in>
# Organization : VLEAD, Virtual-Labs

# Services exposed by CentOSVZAdapter
# http://host-name/api/1.0/vm/create

import json
import urlparse
import urllib
import os.path
import sys
import imp


import tornado.httpserver 
import tornado.ioloop 
import tornado.options 
import tornado.web
from tornado.options import define, options

import Logging

define("port", default=8000, help="run on the given port", type=int)
  

class CreateVMHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Server GET request - Success")

    def post(self):
        Logger.debug("post()")
        post_data = dict(urlparse.parse_qsl(self.request.body))
        Logger.debug("post(); post_data = %s" % post_data)

        vm_id = adapter_instance.create_vm(json.loads(post_data['lab_spec']))
        Logger.debug("created VM id = " + str(vm_id))
        
        (success, result) = adapter_instance.init_vm(vm_id)
	
	if not success:
   	    self.set_status(500)
	    Logger.debug("sucess status returned False from init_vm")
	else:
	   Logger.debug("success status returned True form init_vm")

        Logger.debug("init vm result = " + str(result))
        self.write(result)
        

class DestroyVMHandler(tornado.web.RequestHandler):
    def get(self):
        pass

    def post(self):
        post_data = dict(urlparse.parse_qsl(self.request.body))
        result = adapter_instance.destroy_vm(post_data['vm_id'])
        self.write(result)


class RestartVMHandler(tornado.web.RequestHandler):
    def get(self):
        pass

    def post(self):
        pass    


if __name__ == "__main__": 
    
     #create a logger
    Logging.setup_logging()
    Logger = Logging.LOGGER
    Logger.debug("__main__()")

    tornado.options.parse_command_line()



    try:
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        config_spec = json.loads(open(current_file_path + "/config.json").read())
    except IOError as e:
        Logger.error("unable to load config.json. Exception: " + str(e))
        raise e
    except  Exception as e:
        Logger.error("unable to parse config.json. Exception: " + str(e))
        raise e

   

    #load the adapter class and instantiate the adapter
    adapter_name = config_spec['ADAPTER_NAME']
    module = __import__(adapter_name)
    AdapterClass = getattr(module, adapter_name)
    adapter_instance = AdapterClass()
    

    #make the Adapter log a test message
    adapter_instance.test_logging()

    options.port = config_spec["ADAPTER_PORT"]

    #endpoints of our API to create, destroy and restart the server
    create_uri = "/api/1.0/vm/create"
    destroy_uri = "/api/1.0/vm/destroy"
    restart_uri = "/api/1.0/vm/restart"

    Logger.debug("__main__() PORT=%s, CreateURI=%s, DestroyURI=%s, RestartURI=%s" % \
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
