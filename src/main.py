import warnings
warnings.filterwarnings("ignore")

import signal
import argparse

def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-notify', action='store_true', help="Force notifications to be sent, overriding the config.json. MacOS ONLY!")
  parser.add_argument('-config', action='store_true', help="Print out the current configuration")
  parser.add_argument('-exclude', type=str, help="Add an exclusion case number. Use 'RESET' to reset the file")
  parser.add_argument('-setup', action='store_true', help="Re-write configuration")
  parser.add_argument('-simulate', action='store_true', help="Enter simulation env")
  parser.add_argument('-test', action='store_true', help="Test env - no API calls")
  parser.add_argument('-log', nargs='?', const='info', choices=['info', 'debug'], help="Enable logging. Optional argument: 'debug' for debug-level logging")
  return parser.parse_args()

args = parse_args()
log_level = args.log or None
debug_flag = log_level == 'debug' if log_level else False

from logger import setup_logger, logger as base_logger
if log_level:
  setup_logger(log_level)
logger = base_logger

from config import (
  add_excluded_cases,
  rewrite_configuration,
  load_configuration,
  request_password,
  load_teams_list
)
from helper import handle_shutdown
from exceptions import APIError, ConfigurationError, UnsupportedRole
from handler import role_handler

def main():
  logger.info("Logger initialized with debug=%s and test=%s", debug_flag, args.test)

  try:
    if args.exclude:
      add_excluded_cases(args.exclude)
      return

    if args.setup:
      rewrite_configuration()
      return
    
    if args.simulate:
      from simulation import simulate
      simulate()
      return
    
    logger.info("******************** Config Setup ********************")

    config = load_configuration()
    teamsList = load_teams_list()

    role = config["role"]
    config_debug = config["debug"]
    send_notifications = config["notifications"]["send"]
    engineer_name = config["engineer_name"]
    url = config["api_url"]
    poll_interval = config["poll_interval"]
    sound_notifications = config["notifications"]["sound"]
    color = config["background_color"]

    debug = debug_flag if debug_flag else config_debug
    send_notification = args.notify if args.notify else send_notifications
    if args.config:
      logger.info('Printing config to screen')
      print(f"\n== Current Config == ")
      print(f"> Name/URL:", engineer_name, "/", url)
      print(f"> Products:", [key for key, value in config["products"].items() if value])
      print(f"> Polling Interval:", poll_interval)
      print(f"> Debug:", debug)
      print(f"> Send Notifications:", send_notification)
      print(f"> Notification Sound:", sound_notifications)
      print(f"> Role:", role)
      print(f"> Color:", color)
      handle_shutdown(0)

    logger.info("******************* Setup Complete *******************")
    password = request_password()

    role_handler(role, debug, send_notification, config, password, args.test, teamsList)

  except ConfigurationError as e:
    print(f"Configuration Error: {e}")
  except APIError as e:
    print(f"API Error: {e}")
  except UnsupportedRole as e:
    print(f"Role Error: {e}")
  except Exception as e:
    logger.exception("Unexpected error")
    print(f"Unexpected Error: {e}")

def signal_handler(sig, frame):
  handle_shutdown(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
  main()