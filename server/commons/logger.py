import os
import logging
from logging.handlers import RotatingFileHandler

############### Configure Logger ####################
# path where log files will be saved
LOG_DIR = os.path.join(os.path.expanduser("~"), "JournoLogs")
# Debug level for logger
LOGGING_LEVEL = logging.INFO # logging.DEBUG, logging.INFO, logging.ERROR
# maximum log file backups
MAX_LOG_BACKUPS = 10
# maximum size of log file
MAX_LOG_FILE_SIZE = 500     # in MB
#####################################################

# creating log directory
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE_MAP = {
    "request": "requestserver.log",
    "chat": "chatserver.log",
    "task": "taskserver.log"
}

# global logger instance
logger = None

def initialize(name, loglevel=LOGGING_LEVEL, create_new_logger=False):
    global logger
    if logger is not None and logger.name != "default":
        return logger

    print("Initializing logger...")
    logger = logging.getLogger(name)

    # setting log level
    if loglevel not in [logging.DEBUG, logging.ERROR, logging.INFO, logging.WARNING]:
        print('journo_logger.WARNING("Invalid log level provided. Using default log level.")')
        loglevel = LOGGING_LEVEL
    logger.setLevel(loglevel)

    # preparing formatter to format log messages
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s, %(lineno)d] %(message)s")

    # preparing log file path
    log_file_path = os.path.join(LOG_DIR, LOG_FILE_MAP.get(name, None))
    if not log_file_path:
        if not create_new_logger:
            print('journo_logger.ERROR("Unknown logger name provided. Hence not initializing logger.")')
            return None

        print('journo_logger.WARNING("Unknown logger name providing. Writing logs to "%s.log" file.")'%name)
        log_file_path = "%s.log"%name

    # configuring file handler to handle log file.
    filehandler = RotatingFileHandler(
        log_file_path,
        maxBytes=MAX_LOG_FILE_SIZE*1024*1024,
        backupCount=MAX_LOG_BACKUPS
    )
    filehandler.setFormatter(formatter)
    filehandler.setLevel(LOGGING_LEVEL)

    # configuring stream handler
    streamhandler = logging.StreamHandler()
    streamhandler.setFormatter(formatter)
    streamhandler.setLevel(LOGGING_LEVEL)

    # adding prepared handlers
    logger.addHandler(filehandler)
    logger.addHandler(streamhandler)

    return logger

if logger is None:
    logger = logging.getLogger("default")

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s, %(lineno)d] %(message)s")

    streamhandler = logging.StreamHandler()
    streamhandler.setFormatter(formatter)

    logger.addHandler(streamhandler)
