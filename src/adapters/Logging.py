import os
import logging
from logging.handlers import TimedRotatingFileHandler

current_dir = current_file_path = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = current_dir + "/log/vmmanager.log"       # make log name a setting


def setup_logging():
    LOGGER.setLevel(logging.DEBUG)   # make log level a setting
    # Add the log message handler to the logger
    myhandler = TimedRotatingFileHandler(
                                LOG_PATH, when='midnight', backupCount=5)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s : [%(filename)s:%(lineno)d] : %(message)s',
        datefmt='%Y-%m-%d %I:%M:%S %p')
    myhandler.setFormatter(formatter)
    LOGGER.addHandler(myhandler)


if not os.path.isdir(current_dir + "/log"):
    os.mkdir(current_dir + "/log")
LOGGER = logging.getLogger('AdapterServer')
setup_logging()
LOG_FD = open(LOG_PATH, 'a')
