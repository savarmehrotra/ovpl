from flask import Flask
from api import *
from config import LOG_FILE_DIRECTORY
from config import LOG_FILE
from config import LOG_LEVEL
import os

def create_app():
    # init our app
    app = Flask(__name__)
    app.secret_key = 'development'
    # register blueprints
    app.register_blueprint(api)
    configure_logging(app)
    return app


def configure_logging(app):
    import logging
    import logging.handlers
    formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(filename)s:'
                                  ' %(funcName)s():%(lineno)d: %(message)s')

    # Also error can be sent out via email. So we can also have a SMTPHandler?
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           LOG_FILE_DIRECTORY)

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    log_file = "%s/%s" % (log_dir, LOG_FILE)
    os.system("sudo touch %s" % log_file)
    os.system("sudo chmod 777 %s" % log_file)
    max_size = 1024 * 1024 * 20  # Max Size for a log file: 20MB
    log_handler = logging.handlers.RotatingFileHandler(log_file,
                                                       maxBytes=max_size,
                                                       backupCount=10)
    log_level = LOG_LEVEL
    log_handler.setFormatter(formatter)
    app.logger.addHandler(log_handler)
    app.logger.setLevel(log_level)

#+NAME: run_server
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host='0.0.0.0', threaded=True, port=8080)
