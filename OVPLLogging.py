import logging
from logging.handlers import TimedRotatingFileHandler

LOG_FILENAME = '/root/ovpl/log/ovpl.log'       # make log name a setting

def setup_logging():
    OVPL_LOGGER.setLevel(logging.DEBUG)   # make log level a setting
    # Add the log message handler to the logger
    myhandler = TimedRotatingFileHandler(
                                LOG_FILENAME, when='midnight', backupCount=5)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %I:%M:%S %p')
    myhandler.setFormatter(formatter)
    OVPL_LOGGER.addHandler(myhandler)


OVPL_LOGGER = logging.getLogger('ovpl')
setup_logging()
LOG_FD = open(LOG_FILENAME, 'a')