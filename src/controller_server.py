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

# tornado imports
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options

# ADS imports
from src.http_logging.http_logger import logger
from src.utils.envsetup import EnvSetUp
from src.controller import Controller
from config import authorized_users


define("port", default=8000, help="run on the given port", type=int)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")


class MainHandler(BaseHandler):
    """
    Main Handler is to handle the index page for ControllerServer
    """
    def get(self):
        if not self.current_user:
            self.redirect('/login')
        else:
            self.render('index.html')

    def post(self):
        if not self.current_user:
            self.redirect('/login')
            return

        post_data = dict(urlparse.parse_qsl(self.request.body))
        c = Controller()
        # log the user who is deploying the lab..
        logger.debug("Lab Deployment: deployed by: %s, lab id: %s, URL: %s" %
                     (self.current_user,
                      post_data['lab_id'],
                      post_data['lab_src_url']))

        self.write(c.test_lab(self.current_user, self.post_data['lab_id'],
                              post_data['lab_src_url'],
                              post_data.get('version', None)))


class LoginHandler(BaseHandler):
    """
    LoginHandler will handle logins at /login
    """

    def get(self):
        self.render('login.html')

    def post(self):
        msg = "LoginHandler: Authenticating and authorizing using Persona.."
        logger.debug(msg)
        assertion = self.get_argument("assertion")

        if not assertion:
            logger.debug("Assertion not passed by the client. Aborting.")
            self.write_error(400)
            return

        data = {'assertion': assertion,
                'audience': config_spec["CONTROLLER_CONFIG"]["APP_URL"]}

        # make the auth request to persona
        resp = requests.post(
            config_spec["CONTROLLER_CONFIG"]["PERSONA_VERIFIER"],
            data=data, verify=True)

        if not resp.ok:
            logger.debug("Response from Persona is malformed. Aborting auth.")
            self.write_error(500)
            return

        verified_data = json.loads(resp.content)
        logger.debug("Verified data from Persona: %s" % verified_data)

        if verified_data['status'] != 'okay':
            logger.debug("Persona returned error. Aborting authentication.")
            self.write_error(500)
            return

        user_email = verified_data['email']
        # user exists in our set of authorized users
        if user_email in authorized_users.users:
            logger.debug("Authentication and authorization successful!")
            self.set_secure_cookie('user', user_email)
            self.write({'status': 'okay', 'msg': "Successful login"})
        # user does not exist. Send unauthorized error.
        else:
            logger.debug("User: %s is not authorized. Aborting." % user_email)
            msg = "<b>Oops!</b> You are not authorized to deploy a lab. <br>"
            msg += "<small>Please contact <some> admin for details.</small>"
            self.write({'status': 'error', 'msg': msg})


class LogoutHandler(BaseHandler):
    """
    LogoutHandler will handle logouts at /logout
    """

    def post(self):
        self.clear_cookie('user')
        self.write({'status': 'okay', 'msg': 'logged out'})


if __name__ == "__main__":
    env = EnvSetUp()
    config_spec = env.get_config_spec()
    tornado.options.parse_command_line()
    app = tornado.web.Application(
        handlers=[
            (r"/", MainHandler),
            (r"/login", LoginHandler),
            (r"/logout", LogoutHandler)
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
