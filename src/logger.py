import logging
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUNNING_LOG_FILE = os.path.join(BASE_DIR, '..', 'running.log')

logger = logging.getLogger("custom_logger")
logger.addHandler(logging.NullHandler())

def setup_logger(log_level=None):
    global logger
    if log_level not in ('info', 'debug'):
        return logger

    for h in list(logger.handlers):
        if isinstance(h, logging.FileHandler):
            logger.removeHandler(h)

    logger.setLevel(logging.DEBUG)

    if not logger.handlers or isinstance(logger.handlers[0], logging.NullHandler):
        file_handler = logging.FileHandler(RUNNING_LOG_FILE)
        if log_level == 'debug':
            file_handler.setLevel(logging.DEBUG)
        else:
            file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s [%(levelname)-7s] [%(funcName)s]: %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.propagate = False

    return logger
