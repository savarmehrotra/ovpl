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
import requests
import pymongo

# tornado imports
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
from tornado.options import define, options

# ADS imports
from __init__ import *
from httplogging.http_logger import logger
from utils.envsetup import EnvSetUp
from controller import Controller
from config.adapters import base_config
import json

define("port", default=8000, help="run on the given port", type=int)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    
    def open(self):
        print("Opened Connection to Controller")
    
    def on_message(self,message):
        print("status is :"+message)

    def on_close(self):
        print("Closed Connection to Controller")



class MainHandler(BaseHandler):
 
    def post(self):
        key = base_config.SECRET_KEY
        post_data = json.loads(self.request.body.decode('utf-8'))
        if post_data['key'] != key:
            raise tornado.web.HTTPError(401, "Unauthorized_error")
        c = Controller()
        # log the user who is deploying the lab..
        logger.debug("Lab Deployment: deployed by: %s, lab id: %s, URL: %s" %
                     (post_data['current_user'],
                      post_data['lab_id'],
                      post_data['lab_src_url']))

        ws = WebSocketHandler()
        ws.open()
        ws.on_message()

        self.write(c.test_lab(post_data['current_user'], post_data['lab_id'],
                              post_data['lab_src_url'],
                              post_data.get('version', None)))




if __name__ == "__main__":
    env = EnvSetUp.Instance()
    config_spec = env.get_config_spec()
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/", MainHandler)
        ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        cookie_secret=config_spec["CONTROLLER_CONFIG"]["COOKIE_SECRET"],
        debug=True)

    http_server = tornado.httpserver.HTTPServer(app)
    options.port = config_spec["CONTROLLER_CONFIG"]["SERVER_PORT"]
    logger.debug("ControllerServer: It will run on port : " + str(options.port))
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
