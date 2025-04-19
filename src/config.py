import json
import os
import shutil
from getpass import getpass
from exceptions import ConfigurationError

def load_configuration(config_path="../config.json", credentials_path="../credentials.json"):
  func = "load_configuration()"
  def log(msg): DEBUG(debug, f"{func}: {msg}") if 'debug' in locals() else print(f"{func}: {msg}")

  missing_files = []

  config_template = "../templates/config.json"
  credentials_template = "../templates/credentials.json"

  if not os.path.exists(credentials_path):
    if os.path.exists(credentials_template):
      log("credentials.json not found. Copying from template.")
      shutil.copy(credentials_template, credentials_path)
      missing_files.append('credentials')
    else:
      log(f"Template file {credentials_template} not found.")
      raise ConfigurationError(f"Missing {credentials_path} and no template available.")

  if not os.path.exists(config_path):
    if os.path.exists(config_template):
      log("config.json not found. Copying from template.")
      shutil.copy(config_template, config_path)
      missing_files.append('config')
    else:
      log(f"Template file {config_template} not found.")
      raise ConfigurationError(f"Missing {config_path} and no template available.")

  if missing_files:
    raise ConfigurationError(
      f"The following configuration files were created from templates: {', '.join(missing_files)}. "
      "Please update them and restart the application."
    )

  try:
    with open(config_path, "r") as config_file:
      config = json.load(config_file)
      debug = config.get("debug", False)
      log(f"Reading debug value as {debug}")
      log = lambda msg: DEBUG(debug, f"{func}: {msg}")

      supported_products = config.get("supported_products", {})
      log(f"Reading supported products")

      poll_interval = config.get("poll_interval", 5)
      log(f'Reading polling interval of "{poll_interval}" minutes')

      queries = config.get("queries", {})
      log(f"Reading Salesforce queries")

      send_notifications = config.get("notifications", False)
      log(f"Should notifications be sent: {send_notifications}")

      teams_list = config.get("teams_list", {})
      log(f"Reading teams lists")

      with open(credentials_path, "r") as cred_file:
        salesforce_config = json.load(cred_file)
        log(f"Reading Salesforce credentials")

      return salesforce_config, supported_products, poll_interval, queries, debug, send_notifications, teams_list

  except KeyError as e:
    raise ConfigurationError(f"Missing expected key in the configuration file: {e}")
  except Exception as e:
    print(f"Error loading configuration: {e}")
    raise

def request_password(debug):
  func = "request_password()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")
  log("Requesting password")
  password = getpass("Password required for API: ")
  log("Password entered")
  return password

def DEBUG(debug, message):
  if debug:
    print(f"{message}")

def user_role(config_path="../config.json"):
  try:
    with open(config_path, "r") as config_file:
      config = json.load(config_file)
      role = config.get("role", {})

      return role
  except KeyError as e:
    raise ConfigurationError(f"Missing expected key in the configuration file: {e}")
  except Exception as e:
    print(f"Error loading configuration: {e}")
    raise