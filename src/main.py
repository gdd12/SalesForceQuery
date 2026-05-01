import warnings
import signal
import sys
import os

from args import user_defined_args, argument_handler
from logger import setup_logger, logger as base_logger
from utils.variables import VARS, FileNames
from pathlib import Path

from config.config import Config, load_teams_list
from config.filereg import FileReg
from utils.helper import handle_shutdown
import exceptions as exceptions
from handlers.handler import role_handler
from tools.encryption import generate_encrypted_passwd

def main(debug, testOn, verboseOn=False):
  logger.info("Logger initialized with debug=%s verbose=%s test=%s", debug, verboseOn, testOn)

  try:
    logger.info("******************** Config Setup ********************")
    FileReg().validate()

    config = Config().load()
    teamsList = load_teams_list()

    role = config[VARS.Role]
    send_notifications = config[VARS.Notifications][VARS.SendNotif]

    logger.info("******************* Setup Complete *******************")
    print("\n******************* SalesForceQuery Tool *******************\n")

    if Config().get_config_value("rules.passwd_required_on_startup", default=True):
      generate_encrypted_passwd()

    if (
      not os.path.exists(Path(__file__).resolve().parent.parent / VARS.Config / FileNames.PasswordFile) or
      not os.path.exists(Path(__file__).resolve().parent.parent / VARS.Config / FileNames.KeyFile)
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
  if user_args.get(VARS.Verbose) or Config().get_config_value('debug'):
    log_level = 'debug'
    verboseOn = True

  setup_logger(log_level)

  logger = base_logger

  args = argument_handler(user_args)
  debugOn = True if args.get(VARS.Debug, False) or Config().get_config_value('debug') else False
  testOn = args.get(VARS.Test, False)

  main(debugOn, testOn, verboseOn=verboseOn)