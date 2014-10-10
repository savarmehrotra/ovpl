#!/bin/python

# Services exposed by the VM Manager
# The REST url : 
# http://host-name/api/1.0/disk-usage
# http://host-name/api/1.0/running-time 
# http://host-name/api/1.0/mem-usage
# http://host-name/api/1.0/running-processes
# http://host-name/api/1.0/cpu-load
# http://host-name/api/1.0/execute/<command>

import urlparse
import os
import os.path
import json

# bunch of tornado imports
import tornado.httpserver 
import tornado.ioloop 
import tornado.options 
import tornado.web
from tornado.options import define, options

import Controller
import Logging

# defines the global default arguments like port 
define("port", default=8000, help="run on the given port", type=int)

# this class will handle the root (localhost:8080/) http request
class MainHandler(tornado.web.RequestHandler):
# navigate to index.html using get method	
    def get(self):
        self.render('index.html')
# it passess all the form values (from index.html) to "Controller.py" using post method

    def post(self):
        post_data = dict(urlparse.parse_qsl(self.request.body))
        c = Controller.Controller()
        self.write(c.test_lab(post_data['lab_id'], post_data['lab_src_url'], post_data.get('version', None)))

# here starts your tornado application runnig
if __name__ == "__main__":
# this is to parse your command line arguments
    tornado.options.parse_command_line()
# creating instance for tornado's Application class by passing parameters to handler like regualr expression w.r.t to request handler
    app = tornado.web.Application(
        handlers=[
            (r"/", MainHandler)
        ],
# tornado application will look into this folder while rendering into "index.html" 
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
# " " this folder for javascript, css .. files if any	
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        debug = True)
# here we need to pass tornado's Application class instance to the  httpserver instance
    http_server = tornado.httpserver.HTTPServer(app) 
    current_file_path = os.path.dirname(os.path.abspath(__file__))
# it will read port form .json file
    config_spec = json.loads(open(current_file_path + "/../config/config.json").read())
    options.port = config_spec["CONTROLLER_CONFIG"]["SERVER_PORT"]
# this is for storing loggin
    Logging.LOGGER.debug("ControllerServer: It will run on port : " + str(options.port))
# here http server will listen to the given port
    http_server.listen(options.port) 
# this will start your tornado application
    tornado.ioloop.IOLoop.instance().start()
