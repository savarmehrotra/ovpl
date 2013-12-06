# Author : Avinash <a@vlabs.ac.in>
# Organization : VLEAD, Virtual-Labs

import time
import BaseHTTPServer
import urlparse
import urllib 
import SocketServer
import threading

import CentOSVZAdapter
from VMSpec import VMSpec

HOST_NAME = '10.4.12.21' #base1 machine's IP
PORT_NUMBER = 80 


class CentOSVZAdapterHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """  """
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        pass

    def do_POST(self):
        length = int(self.headers['Content-Length'])
        post_data = dict(urlparse.parse_qsl(self.rfile.read(length)))
        vm_spec = VMSpec(post_data)
        #platform_adapter = CentOSVZAdapter()
        response = CentOSVZAdapter.create_vm("99100", vm_spec)
        #CentOSVZAdapter.destroy_vm("99100")
        self.wfile.write(response)
        return


class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    """ Handle requests in a separate thread. """
    pass


if __name__ == '__main__':
    # httpd = ThreadedHTTPServer((HOST_NAME, PORT_NUMBER), CentOSVZAdapterHandler)
    httpd = BaseHTTPServer.HTTPServer((HOST_NAME, PORT_NUMBER), CentOSVZAdapterHandler)

    try:
        httpd.serve_forever()
        print "Server Started - %s:%s with the thread :%s" % (HOST_NAME, PORT_NUMBER, server_thread.name)
    except KeyboardInterrupt:
        httpd.server_close()
    print "Server Stopped - %s:%s" % (HOST_NAME, PORT_NUMBER)