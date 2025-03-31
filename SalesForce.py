from requests.auth import HTTPBasicAuth
from collections import defaultdict
from datetime import datetime
import requests
import shutil
import time
import json
import sys
import os

def load_configuration(config_path="config.json", credentials_path="credentials.json"):
  func = "load_configuration()"
  if not os.path.exists(credentials_path):
    template_path = "templates/credentials.json"
    if os.path.exists(template_path):
      print(f"{func}: credentials.json not found. Copying from template.")
      shutil.copy(template_path, credentials_path)
    else:
      print(f"{func}: Template file {template_path} not found.")
      return None, None

  try:
    with open(config_path, "r") as config_file:
      config = json.load(config_file)
      debug = config.get("debug", False)
      debug_log(debug, f'{func}: Loaded debug value as {debug}')
      
      supported_products = config.get("supported_products", {})
      debug_log(debug, f'{func}: Loaded supported products from {config_path}')
      
      poll_interval = config.get("poll_interval", 5)
      debug_log(debug, f'{func}: Loaded polling interval from {config_path}')
      
      queries = config.get("queries", {})
      debug_log(debug, f'{func}: Loaded Salesforce queries from {config_path}')
      
      debug_log(debug, f'{func}: Returning configuration to the main() function')
      
      with open(credentials_path, "r") as cred_file:
        salesforce_config = json.load(cred_file)
        debug_log(debug, f'{func}: Loaded Salesforce credentials from {credentials_path}')
          
      return salesforce_config, supported_products, poll_interval, queries, debug

  except Exception as e:
    print(f"Error loading configuration: {e}")
    return None, None

def http_handler(api_url, username, password, query, debug):
  func = "http_handler()"
  debug_log(debug, f'{func}: Started')
  debug_log(debug, f'{func}: Setting up basic authentication string via Base64 encoding of Username:Password')
  auth = HTTPBasicAuth(username, password)
  debug_log(debug, f'{func}: Making HTTP request with the query:')
  debug_log(debug, f'{func}: {query}')
  response = requests.get(api_url, headers={"Content-Type": "application/json"}, auth=auth, params={"q": query})

  if response.status_code == 200:
    debug_log(debug, f'{func}: HTTP {response.status_code}')
    return response.json().get('records', []) and debug_log(debug, f'{func}: Finished')
  if response.status_code == 401 or 400:
    debug_log(debug, f'{func}: HTTP {response.status_code}. Exiting due to credentials errors.')
    print(f"HTTP Error: {response.status_code} credential issue. Update username/password in config.json")
    debug_log(debug, f'{func}: Finished')
    sys.exit(1)
  else:
    print(f"Error fetching data from Salesforce: {response.status_code} - {response.text}")
    return [] and debug_log(debug, f'{func}: Finished')

def fetch_team_cases(api_url, username, password, supported_products_dict, query, debug):
  func = "fetch_team_cases()"
  debug_log(debug, f'{func}: Started')
  debug_log(debug, f'{func}: List comprehension started for the configured supported products')
  supported_products = [product for product, is_supported in supported_products_dict.items() if is_supported]
  
  if not supported_products:
    debug_log(debug, f'{func}: No products in the configuration file were set to true. Exiting.')
    print("No supported products found in the configuration. Please update the config.json file and restart.")
    debug_log(debug, f'{func}: Finished')
    sys.exit(1)

  debug_log(debug, f'{func}: Joining the supported products in a valid string for injection into the query')
  product_list = "', '".join(supported_products)
  product_list = f"'{product_list}'"

  debug_log(debug, f'{func}: Injecting valid product list into the query')
  query = query.format(product_name=product_list)

  debug_log(debug, f'{func}: Calling the HTTP handler function')
  return http_handler(api_url, username, password, query, debug) and debug_log(debug, f'{func}: Finished')


def fetch_personal_cases(api_url, username, password, query, debug):
  func = "fetch_personal_cases()"
  debug_log(debug, f'{func}: Calling the HTTP handler function')
  return http_handler(api_url, username, password, query, debug) and debug_log(debug, f'{func}: Finished')
def display_team(cases):
  product_count = defaultdict(int)

  for case in cases:
    product = case.get('Product__r', {}).get('Name', 'No Product')
    product_count[product] += 1

  if product_count:
    for product, count in product_count.items():
      print(f"  {count} new {product} case(s)")
  else:
    print(" No cases in the queue")

def display_personal(cases):
  InSupport = 0
  New = 0
  NeedsCommitment = 0
  for case in cases:
    status = case.get('Status')
    commitment_time = case.get('Time_Before_Next_Update_Commitment__c')

    if commitment_time < 1 and status != 'New':
      NeedsCommitment += 1
    if status == "In Support":
      InSupport += 1
    if status == "New":
      New += 1
  print("\n")
  if InSupport > 0:
    print(f"  {InSupport} case(s) are In Support")
  if New > 0:
    print(f"  {New} case(s) need an IC")
  if NeedsCommitment > 0:
    print(f"  {NeedsCommitment} case(s) need an update in 24 hours")

def clear_screen():
  if os.name == 'nt':
    os.system('cls')
  else:
    os.system('clear')

def debug_log(debug, message):
  if debug:
    print(f"{message}")

def main():
  func = 'main()'
  salesforce_config, supported_products_dict, poll_interval, queries, debug = load_configuration()

  debug_log(debug, f'{func}: Started')
  debug_log(debug, f'{func}: Destructuring the SalesForce config to validate the values')
  api_url = salesforce_config.get("url")
  username = salesforce_config.get("username")
  password = salesforce_config.get("password")
  engineer_name = salesforce_config.get("engineer_name")
  team_query = queries["team"]
  personal_query = queries["personal"]

  if not api_url:
    debug_log(debug, f'{func}: api_url is set to "{api_url}" which is not an allowed value')
    print("Missing Salesforce API in the configuration file.")
    debug_log(debug, f'{func}: Finished')
    return
  if not username or not password:
    debug_log(debug, f'{func}: Username or password is not configured which is required for the API call')
    print("Missing credentials in the configuration file.")
    debug_log(debug, f'{func}: Finished')
    return
  if not engineer_name:
    debug_log(debug, f'{func}: engineer_name is set to "{engineer_name}" which is not an allowed value')
    print("Missing engineer name in the configuration file.")
    debug_log(debug, f'{func}: Finished')
    return
  debug_log(debug, f'{func}: Setting the loaded engineer_name of "{engineer_name}" to the personal_query')
  personal_query = personal_query.format(engineer_name=engineer_name)

  while True:
    if not debug:
      clear_screen()
      print(f"Fetching batch @ {(datetime.now()).strftime('%a %b %d %H:%M:%S')}\n")

    debug_log(debug, f'{func}: Calling the API for the configured TEAM query')
    team_cases = fetch_team_cases(api_url, username, password, supported_products_dict, team_query, debug)
    debug_log(debug, f'{func}: Calling the API for the configured PERSONAL query')
    personal_cases = fetch_personal_cases(api_url, username, password, personal_query, debug)

    if not team_cases:
      print(" No cases in the queue")
    else:
      display_team(team_cases)

    if not personal_cases:
      print(" You have no assigned cases")
    else:
      display_personal(personal_cases)

    debug_log(debug, f'{func}: Finished')
    print(f"\nNext poll in {poll_interval} minutes...")
    time.sleep(poll_interval * 60)

if __name__ == "__main__":
  main()