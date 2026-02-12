import warnings
import signal
import argparse

from args import user_defined_args, argument_handler
from logger import setup_logger, setup_process_logger, logger as base_logger, process
from variables import VARS

from config import (
  load_configuration,
  request_password,
  load_teams_list,
  get_config_value
)
from helper import handle_shutdown
from exceptions import APIError, ConfigurationError, UnsupportedRole
from handler import role_handler

def main(debug, testOn, verboseOn=False):
  logger.info("Logger initialized with debug=%s verbose=%s test=%s", debug, verboseOn, testOn)
  process.info("Processing logger initialized with debug=%s verbose=%s and test=%s", debug, verboseOn, testOn)

  try:
    logger.info("******************** Config Setup ********************")
    config = load_configuration()
    teamsList = load_teams_list()

    role = config[VARS.Role]
    send_notifications = config[VARS.Notifications][VARS.SendNotif]

    logger.info("******************* Setup Complete *******************")
    print("\n******************* SalesForceQuery Tool *******************\n")

    role_handler(role, debug, send_notifications, config, testOn, teamsList)

  except ConfigurationError as e:
    print(f"Configuration Error: {e}")
  except APIError as e:
    print(f"API Error: {e}")
  except UnsupportedRole as e:
    print(f"Role Error: {e}")
  except TypeError as e:
    logger.exception(f"TypeError {e}")
    print(f"TypeError {e}")
  except Exception as e:
    logger.exception(f"UnexpectedError: {e}")
    print(f"Exception {e}")

def signal_handler(sig, frame):
  handle_shutdown(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
  user_args = user_defined_args()
  verboseOn = False
  log_level = None

  if user_args['debug']:
    log_level = 'info'
  if user_args['debug_verbose'] or get_config_value('debug'):
    log_level = 'debug'
    verboseOn = True

  setup_logger(log_level)
  setup_process_logger(log_level)

  logger = base_logger

  args = argument_handler(user_args)
  debugOn = True if args.get(VARS.Debug, False) or get_config_value('debug') else False
  testOn = args.get(VARS.Test, False)

  main(debugOn, testOn, verboseOn=verboseOn)