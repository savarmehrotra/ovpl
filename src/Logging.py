import os
import logging
from logging.handlers import TimedRotatingFileHandler
import json

LOG_FILENAME = 'log/ovpl.log'       # make log name a setting

def setup_logging():
    LOGGER.setLevel(logging.DEBUG)   # make log level a setting
    # Add the log message handler to the logger
    myhandler = TimedRotatingFileHandler(
                                LOG_FILENAME, when='midnight', backupCount=5)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %I:%M:%S %p')
    myhandler.setFormatter(formatter)
    LOGGER.addHandler(myhandler)

config_spec = json.loads(open("../config/config.json").read())
LOG_FILENAME = config_spec["CONTROLLER_CONFIG"]["LOG_FILENAME"]

nodes = LOG_FILENAME.split("/")
nodes = nodes[1:-1]   #remove the first and the last elements
dir_path = ""
for node in nodes:
    dir_path = dir_path + "/" + node

if not os.path.isdir(dir_path):
    os.makedirs(dir_path)

LOGGER = logging.getLogger('ovpl')
setup_logging()
LOG_FD = open(LOG_FILENAME, 'a')
