import signal
import time
import sys
import os
from config import load_configuration, DEBUG, request_password
from api import http_handler
from display import clear_screen, handle_shutdown, display_personal, display_team, display_opened_today
from datetime import datetime
from exceptions import APIError, ConfigurationError
from notification import notify

def main():
  func = 'main()'
  try:
    salesforce_config, supported_products_dict, poll_interval, queries, debug, send_notifications = load_configuration()

    DEBUG(debug, f'{func}: Started')
    DEBUG(debug, f'{func}: Destructuring the SalesForce config to validate the values')

    api_url = salesforce_config.get("url")
    username = salesforce_config.get("username")
    engineer_name = salesforce_config.get("engineer_name")
    team_query = queries["team"]
    personal_query = queries["personal"]
    opened_today_query = queries["opened_today"]

    if not api_url:
      DEBUG(debug, f'{func}: api_url is set to "{api_url}" which is not an allowed value')
      raise ConfigurationError("Missing Salesforce API in the configuration file.")
    if not username:
      raise ConfigurationError("Missing username in the configuration file.")
    if not engineer_name:
      raise ConfigurationError("Missing engineer name in the configuration file.")
    DEBUG(debug, f'{func}: Setting the loaded engineer_name of "{engineer_name}" to the personal_query')
    personal_query = personal_query.format(engineer_name=engineer_name)

    password = request_password(debug)
    DEBUG(debug, f'{func}: The following has all been loaded into memory:')
    DEBUG(debug, f'{func}:  - Supported products')
    DEBUG(debug, f'{func}:  - Polling interval')
    DEBUG(debug, f"{func}:  - Engineer's name")
    DEBUG(debug, f'{func}:  - All queries')
    DEBUG(debug, f'{func}:  - Debug value')
    DEBUG(debug, f'{func}:  - Username')
    DEBUG(debug, f'{func}:  - Password')
    DEBUG(debug, f'{func}:  - API URL')
    DEBUG(debug, f'{func}:  - Sending notification')
    while True:
      """
      This is the main looping function anything that needs to be called 
      every polling interval needs to be in this loop.
      """
      if not debug:
        clear_screen()
        print(f"Fetching batch @ {(datetime.now()).strftime('%a %b %d %H:%M:%S')}\n")

      DEBUG(debug, f'{func}: Calling the API for the configured TEAM query')
      team_cases = fetch_cases(api_url, username, password, supported_products_dict, team_query, debug)
      DEBUG(debug, f'{func}: Calling the API for the configured PERSONAL query')
      personal_cases = fetch_cases(api_url, username, password, supported_products_dict, personal_query, debug)
      DEBUG(debug, f'{func}: Calling the API for the configured OPENED_TODAY query')
      opened_today_cases = fetch_cases(api_url, username, password, supported_products_dict, opened_today_query, debug)

      if not team_cases:
        print("  No cases in the queue")
      else:
        display_team(team_cases, debug)

      if personal_cases:
        display_personal(personal_cases, debug)

      if opened_today_cases:
        display_opened_today(opened_today_cases, debug)

      if os.name != 'nt' and send_notifications:
        notify(team_cases, debug)
      if not debug: print(f"\nNext poll in {poll_interval} minutes...")
      DEBUG(debug, f'{func}: Clock for {poll_interval} minutes has begun.')
      time.sleep(poll_interval * 60)

  except ConfigurationError as e:
    print(f"Configuration Error: {e}")
  except APIError as e:
    print(f"API Error: {e}")
  except Exception as e:
    print(f"Unexpected Error: {e}")
    sys.exit(1)

def fetch_cases(api_url, username, password, supported_products_dict, query, debug):
  func = "fetch_cases()"
  DEBUG(debug, f'{func}: Started')

  supported_products = [product for product, is_supported in supported_products_dict.items() if is_supported]
  if not supported_products:
    DEBUG(debug, f'{func}: No products in the configuration file were set to true. Exiting.')
    raise ConfigurationError(f"At least one product must be 'true' in the supported_products configuration.")

  DEBUG(debug, f'{func}: Joining the supported products in a valid string and injecting into the query')
  product_list = "', '".join(supported_products)
  product_list = f"'{product_list}'"
  query = query.format(product_name=product_list)

  DEBUG(debug, f'{func}: Calling the HTTP handler function')
  return http_handler(api_url, username, password, query, debug)

signal.signal(signal.SIGINT, handle_shutdown)

if __name__ == "__main__":
	main()