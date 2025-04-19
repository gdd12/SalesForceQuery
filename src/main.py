import signal
import time
import sys
import os
from config import (
  load_configuration,
  DEBUG,
  request_password,
  user_role
)
from api import http_handler
from display import (
  clear_screen,
  handle_shutdown,
  display_personal,
  display_team,
  display_opened_today,
  info_logger,
  title,
  display_team_needs_commitment
)
from datetime import datetime
from exceptions import APIError, ConfigurationError, UnsupportedRole
from notification import notify
from helper import concat_team_list

def main():
  args = info_logger()
  func = 'main()'
  try:
    config = load_configuration()
    role = user_role()
    salesforce_config, supported_products_dict, poll_interval, queries, config_debug, send_notifications, teams_list = config

    debug = args.debug if args.debug else config_debug
    send_notification = args.notify if args.notify else send_notifications

    def log(msg): DEBUG(debug, f"{func}: {msg}")

    log("Started")
    log("Destructuring the SalesForce config to validate the values")

    api_url = salesforce_config.get("url")
    username = salesforce_config.get("username")
    engineer_name = salesforce_config.get("engineer_name")
    team_query = queries["team_queue"]
    personal_query = queries["personal_queue"]
    opened_today_query = queries["opened_today"]
    needs_commitment_query = queries["needs_commitment"]
    team_needs_commitment_query = queries["team_needs_commitment"]

    if role.upper() == "MANAGER":
      names = concat_team_list(teams_list)
      team_needs_commitment_query = team_needs_commitment_query.format(team_list=names)

    if not api_url:
      log(f'api_url is set to "{api_url}" which is not an allowed value')
      raise ConfigurationError("Missing Salesforce API in the configuration file.")
    if not username:
      raise ConfigurationError("Missing username in the configuration file.")
    if not engineer_name:
      raise ConfigurationError("Missing engineer name in the configuration file.")
    log(f'Setting the loaded engineer_name of "{engineer_name}" to the personal_query')
    personal_query = personal_query.format(engineer_name=engineer_name)

    password = request_password(debug)
    log("The following has all been loaded into memory:")
    for item in [
      "Supported products", "Polling interval", "Engineer's name", "All queries",
      "Debug value", "Username", "Password", "API URL", "Sending notification", "User role"
    ]:
      log(f"  - {item}")

    while True:
      if not debug:
        clear_screen()
        header = title()
        print(header)
        print(f"                  Fetching batch @ {(datetime.now()).strftime('%a %b %d %H:%M:%S')}")
        print(f"                        Next poll in {poll_interval} minutes...")

      if role.upper() == "ENGINEER":
        run_queries_for_tse(api_url, username, password, supported_products_dict, team_query, personal_query, opened_today_query, send_notification, debug)
      elif role.upper() == "MANAGER":
        run_queries_for_manager(api_url, username, password, team_needs_commitment_query, debug)
      else:
        raise UnsupportedRole(f'Unsupported role: "{role}"')

      log(f"Clock for {poll_interval} minutes has begun.")
      time.sleep(poll_interval * 60)

  except ConfigurationError as e:
    print(f"Configuration Error: {e}")
  except APIError as e:
    print(f"API Error: {e}")
  except UnsupportedRole as e:
    print(f"Role Error: {e}")
  except Exception as e:
    print(f"Unexpected Error: {e}")
    sys.exit(1)

def fetch_cases_tse(api_url, username, password, supported_products_dict, query, debug):
  func = "fetch_cases_tse()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")
  log("Started")

  supported_products = [product for product, is_supported in supported_products_dict.items() if is_supported]
  if not supported_products:
    log("No products in the configuration file were set to true. Exiting.")
    raise ConfigurationError("At least one product must be 'true' in the supported_products configuration.")

  product_list = "', '".join(supported_products)
  product_list = f"'{product_list}'"
  query = query.format(product_name=product_list)

  log("Calling the HTTP handler function")
  return http_handler(api_url, username, password, query, debug)

def fetch_cases_manager(api_url, username, password, query, debug):
  func = "fetch_cases_manager()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")
  log("Started")

  log("Calling the HTTP handler function")
  return http_handler(api_url, username, password, query, debug)

def run_queries_for_tse(api_url, username, password, supported_products_dict, team_query, personal_query, opened_today_query, send_notification, debug):
  func = "run_queries_for_tse()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")
  log("Calling the API for the configured TEAM query")
  team_cases = fetch_cases_tse(api_url, username, password, supported_products_dict, team_query, debug)
  log("Calling the API for the configured PERSONAL query")
  personal_cases = fetch_cases_tse(api_url, username, password, supported_products_dict, personal_query, debug)
  log("Calling the API for the configured OPENED_TODAY query")
  opened_today_cases = fetch_cases_tse(api_url, username, password, supported_products_dict, opened_today_query, debug)

  display_team(team_cases, debug)

  if personal_cases:
    display_personal(personal_cases, debug)

  if opened_today_cases:
    display_opened_today(opened_today_cases, debug)

  if os.name != 'nt' and send_notification:
    log(f"User is running {os.name} and sending notifications is set to {send_notification}. Calling notify()")
    notify(team_cases, debug)

def run_queries_for_manager(api_url, username, password, team_needs_commitment_query, debug):
  func = "run_queries_for_manager()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")

  log("Calling the API for the configured TEAM_NEEDS_COMMITMENT query")
  needs_commitment = fetch_cases_manager(api_url, username, password, team_needs_commitment_query, debug)

  display_team_needs_commitment(needs_commitment, debug)

signal.signal(signal.SIGINT, handle_shutdown)

if __name__ == "__main__":
	main()