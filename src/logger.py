import logging, sys
from pathlib import Path
from utils.variables import FileNames
from logging.handlers import RotatingFileHandler

LOG_FILE = Path(__file__).resolve().parent.parent / FileNames.RunningLog
logger = logging.getLogger("logger")

def setup_logger(
    log_level=None,
    max_mb=2,
    backup_count=1
):
    global logger
    if log_level not in ('info', 'debug'):
        return logger

    for h in list(logger.handlers):
        if isinstance(h, logging.FileHandler):
            logger.removeHandler(h)

    logger.setLevel(logging.DEBUG)

    formatter_file = logging.Formatter('%(asctime)s - %(levelname)-6s [%(module)s] (%(funcName)s) - %(message)s')
    formatter_console = logging.Formatter('%(message)s')

    max_bytes = max_mb * 1024 * 1024

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8"
    )

    if not logger.handlers or isinstance(logger.handlers[0], logging.NullHandler):
        console_handler = logging.StreamHandler(sys.stdout)
        if log_level == 'debug':
            file_handler.setLevel(logging.DEBUG)
        else:
            file_handler.setLevel(logging.INFO)
    
        file_handler.setFormatter(formatter_file)
        
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter_console)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        logger.propagate = False

    return logger
