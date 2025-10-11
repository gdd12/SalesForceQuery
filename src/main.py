import warnings
warnings.filterwarnings("ignore")

import signal
import argparse
from config import add_excluded_cases, rewrite_configuration

def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument('-debug', action='store_true', help="Enable debug logging into a running.log file")
  parser.add_argument('-notify', action='store_true', help="Force notifications to be sent, overriding the config.json. MacOS ONLY!")
  parser.add_argument('-config', action='store_true', help="Print out the current configuration")
  parser.add_argument('-exclude', type=str, help="Add an exclusion case number. Use 'RESET' to reset the file")
  parser.add_argument('-setup', action='store_true', help="Re-write configuration")
  parser.add_argument('-simulate', action='store_true', help="Enter simulation env")
  return parser.parse_args()

args = parse_args()
debug_flag = args.debug

from logger import setup_logger
logger = setup_logger(debug_flag)

from config import (
  load_configuration,
  request_password
)
from helper import handle_shutdown
from exceptions import APIError, ConfigurationError, UnsupportedRole
from handler import role_handler

def main():
  logger.info("Logger initialized with debug=%s", debug_flag)

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
    logger.info("******************************************************")

    config = load_configuration()
    role = config[8]
    config_debug = config[4]
    send_notifications = config[5]

    debug = args.debug if args.debug else config_debug
    send_notification = args.notify if args.notify else send_notifications
    if args.config:
      logger.info('Printing config to screen')
      print(f"\n== Current Config == ")
      print(f"> Name/URL:", config[0].get("engineer_name"), "/", config[0].get("url"))
      print(f"> Products:", [key for key, value in config[1].items() if value])
      print(f"> Polling Interval:", config[2])
      print(f"> Debug:", config[4])
      print(f"> Send Notifications:", config[5])
      print(f"> Notification Sound:", config[7])
      print(f"> Role:", config[8])
      print(f"> Color:", config[9])
      handle_shutdown(0)

    logger.info("******************* Setup Complete *******************")
    logger.info("******************************************************")
    password = request_password()

    role_handler(role, debug, send_notification, config, password)

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