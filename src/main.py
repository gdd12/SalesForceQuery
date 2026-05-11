import warnings
import signal
import sys
import os

from args import user_defined_args, argument_handler
from logger import setup_logger, logger as base_logger
from utils.variables import VARS, FileNames
from pathlib import Path

from config.config import Config
from config.team import Team
from config.filereg import FileReg
from utils.helper import handle_shutdown
import exceptions as exceptions
from handlers.handler import role_handler
from tools.encryption import generate_encrypted_passwd
from tools.counter import Counter
from display.common import CommonDisplay

def startup(debug, testOn, verboseOn=False):
  logger.info("Logger initialized with debug=%s verbose=%s test=%s", debug, verboseOn, testOn)
  CommonDisplay().main_banner()

  try:
    logger.info("******************** Config Setup ********************")

    INSTANCES = {
      FileReg(),
      Config(),
      Team()
    }

    for inst in INSTANCES:
      logger.debug(f"Initializing class %s", inst.__class__.__name__)
      inst.init()

  except Exception as e:
    logger.error(f"FATAL - Configuration validation failed")
    logger.error(f"{type(e).__name__}: {e}")
    print("\nThe above exception(s) may be recoverable by performing a clean operation: main.py -z\n")
    raise

  try:
    logger.info("******************* Setup Complete *******************")

    config = Config().load_file()
    teamsList = Team().load_teams_list()

    role = config[VARS.Role]
    send_notifications = config[VARS.Notifications][VARS.SendNotif]

    if (
      not os.path.exists(Path(__file__).resolve().parent.parent / VARS.Config / FileNames.PasswordFile) or
      not os.path.exists(Path(__file__).resolve().parent.parent / VARS.Config / FileNames.KeyFile) or
      not Counter().ok()
    ): generate_encrypted_passwd()
    
    role_handler(role, debug, send_notifications, config, testOn, teamsList)

  except Exception as e:
    logger.exception(f"{type(e).__name__}: {e}")
    print(f"{type(e).__name__}: {e}")

def signal_handler(sig, frame):
  handle_shutdown(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
  user_args = user_defined_args(sys.argv)
  verboseOn = False
  log_level = None

  if user_args.get(VARS.Debug):
    log_level = 'info'
  if user_args.get(VARS.Verbose) or Config().get_config_value('debug', default=False):
    log_level = 'debug'
    verboseOn = True

  setup_logger(log_level)

  logger = base_logger

  args = argument_handler(user_args)
  debugOn = True if args.get(VARS.Debug, False) or Config().get_config_value('debug', default=False) else False
  testOn = args.get(VARS.Test, False)

  startup(debugOn, testOn, verboseOn=verboseOn)