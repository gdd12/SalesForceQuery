import json
import os
import shutil
from getpass import getpass
from exceptions import ConfigurationError

def load_configuration(config_path="../config.json", credentials_path="../credentials.json"):
  func = "load_configuration()"
  missing_files = []

  config_template = "../templates/config.json"
  credentials_template = "../templates/credentials.json"

  if not os.path.exists(credentials_path):
    if os.path.exists(credentials_template):
      print(f"{func}: credentials.json not found. Copying from template.")
      shutil.copy(credentials_template, credentials_path)
      missing_files.append('credentials')
    else:
      print(f"{func}: Template file {credentials_template} not found.")
      raise ConfigurationError(f"Missing {credentials_path} and no template available.")

  if not os.path.exists(config_path):
    if os.path.exists(config_template):
      print(f"{func}: config.json not found. Copying from template.")
      shutil.copy(config_template, config_path)
      missing_files.append('config')
    else:
      print(f"{func}: Template file {config_template} not found.")
      raise ConfigurationError(f"Missing {config_path} and no template available.")

  if missing_files:
    raise ConfigurationError(f"The following configuration files were created from templates: {', '.join(missing_files)}. Please update them and restart the application.")

  try:
    with open(config_path, "r") as config_file:
      config = json.load(config_file)
      debug = config.get("debug", False)
      DEBUG(debug, f'{func}: Reading debug value as {debug}')

      supported_products = config.get("supported_products", {})
      DEBUG(debug, f'{func}: Reading products from {config_path}')

      poll_interval = config.get("poll_interval", 5)
      DEBUG(debug, f'{func}: Reading polling interval from {config_path} of "{poll_interval}" minutes')

      queries = config.get("queries", {})
      DEBUG(debug, f'{func}: Reading Salesforce queries from {config_path}')

      send_notifications = config.get("notifications", False)
      DEBUG(debug, f'{func}: Reading Notification boolean of {send_notifications}')

      with open(credentials_path, "r") as cred_file:
        salesforce_config = json.load(cred_file)
        DEBUG(debug, f'{func}: Reading Salesforce credentials from {credentials_path}')

      DEBUG(debug, f'{func}: Returning all configuration values to main()')
      return salesforce_config, supported_products, poll_interval, queries, debug, send_notifications

  except KeyError as e:
    raise ConfigurationError(f"Missing expected key in the configuration file: {e}")
  except Exception as e:
    print(f"Error loading configuration: {e}")
    raise

def request_password(debug):
  func = "request_password()"
  DEBUG(debug, f'{func}: Requesting password')
  password = getpass("Password required for API: ")
  DEBUG(debug, f'{func}: Password entered')
  return password

def DEBUG(debug, message):
  if debug:
    print(f"{message}")