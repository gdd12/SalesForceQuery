import logging
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, '..', 'running.log')

logger = logging.getLogger("custom_logger")
logger.addHandler(logging.NullHandler())

def setup_logger(log_level=None):
    global logger
    if log_level not in ('info', 'debug'):
        return logger
    logger.setLevel(logging.DEBUG)

    if not logger.handlers or isinstance(logger.handlers[0], logging.NullHandler):
        file_handler = logging.FileHandler(LOG_FILE)
        if log_level == 'debug':
            file_handler.setLevel(logging.DEBUG)
        else:
            file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(funcName)s]: %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    return logger
