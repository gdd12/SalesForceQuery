import logging
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, '..', 'running.log')

def setup_logger(debug_enabled=False):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE)
        if debug_enabled:
            file_handler.setLevel(logging.DEBUG)
        else:
            file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(funcName)s]: %(message)s')
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

    return logger
