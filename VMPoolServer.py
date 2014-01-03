#!/bin/python

# Services exposed by the VM Pool Server
# The REST url : 
# http://host-name/api/1.0/vm/create
# http://host-name/api/1.0/vm/destroy/<vm-id>

# bunch of tornado imports
import tornado.httpserver 
import tornado.ioloop 
import tornado.options 
import tornado.web
from tornado.options import define, options

import VMManager
import VMPool

define("port", default=8000, help="run on the given port", type=int)


class CreateVMHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('Send POST request to create a new VM')

    def post(self):
        pool = VMPool.VMPool("http://localhost", "8000")
        pool.create_vm(None)


class DestroyVMHandler(tornado.web.RequestHandler):
    def get(self):
        self.write('Send DELETE request to destroy the VM')

    def post(self):
        self.write('Send DELETE request to destroy the VM')

    def delete(self, vm_id):
        VMPool.destroy_vm(vm_id)


if __name__ == "__main__": 
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/api/1.0/vm/create", CreateVMHandler),
            (r"/api/1.0/vm/destroy/(\w+)", DestroyVMHandler)
        ],
        debug = True)
    http_server = tornado.httpserver.HTTPServer(app) 
    http_server.listen(options.port) 
    tornado.ioloop.IOLoop.instance().start()