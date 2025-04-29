import json
import os
import shutil
from getpass import getpass
from exceptions import ConfigurationError

config_path = "../config.json"
credentials_path = "../credentials.json"
config_template = "../templates/config.json"
credentials_template = "../templates/credentials.json"

def load_configuration():
  func = "load_configuration()"
  def log(msg): DEBUG(debug, f"{func}: {msg}") if 'debug' in locals() else print(f"{func}: {msg}")

  missing_files = []

  if not os.path.exists(credentials_path):
    if os.path.exists(credentials_template):
      log("credentials.json not found. Copying from template.")
      shutil.copy(credentials_template, credentials_path)
      missing_files.append('credentials')
    else:
      log(f"Template file {credentials_template} not found.")
      raise ConfigurationError(f"{func}; Missing {credentials_path} and no template available.")

  if not os.path.exists(config_path):
    if os.path.exists(config_template):
      log("config.json not found. Copying from template.")
      shutil.copy(config_template, config_path)
      missing_files.append('config')
    else:
      log(f"Template file {config_template} not found.")
      raise ConfigurationError(f"{func}; Missing {config_path} and no template available.")

  if missing_files:
    raise ConfigurationError(
      f"{func}; The following configuration files were created from templates: {', '.join(missing_files)}. "
      "Please update them and restart the application."
    )

  try:
    with open(config_path, "r") as config_file:
      config = json.load(config_file)

      configurable = config.get("CONFIGURABLE", {})
      queries = config.get("DO_NOT_TOUCH", {}).get("queries", {})

      debug = configurable.get("debug", False)
      log(f"Reading debug value as {debug}")
      log = lambda msg: DEBUG(debug, f"{func}: {msg}")

      supported_products = configurable.get("supported_products", {})
      log(f"Reading supported products")
      poll_interval = configurable.get("poll_interval", 5)
      log(f'Reading polling interval of "{poll_interval}" minutes')
      queries = config.get("DO_NOT_TOUCH", {}).get("queries", {})
      log(f"Reading Salesforce queries")
      send_notifications = configurable.get("notifications", {}).get("send", False)
      log(f"Should notifications be sent: {send_notifications}")
      sound_notifications = configurable.get("notifications", {}).get("sound", False)
      log(f"Notification sound: {sound_notifications}")
      teams_list = configurable.get("teams_list", {})
      log(f"Reading teams lists")

      with open(credentials_path, "r") as cred_file:
        salesforce_config = json.load(cred_file)
        log(f"Reading Salesforce credentials")
      
      background_color()
      return salesforce_config, supported_products, poll_interval, queries, debug, send_notifications, teams_list, sound_notifications

  except KeyError as e:
    raise ConfigurationError(f"{func}; Missing expected key in the configuration file: {e}")

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

def user_role():
  func = "user_role()"
  try:
    with open(config_path, "r") as config_file:
      config = json.load(config_file)
      role = config.get("CONFIGURABLE", {}).get("role",)

      return role
  except KeyError as e:
    raise ConfigurationError(f"{func}; Missing expected key in the configuration file: {e}")
  except Exception as e:
    print(f"Error loading configuration: {e}")
    raise

def background_color():
  func = "background_color()"
  acceptable_colors = ["black","red","green","yellow","blue","magenta","cyan","white","bright_black","bright_red","bright_green","bright_yellow","bright_blue","bright_magenta","bright_cyan","bright_white"]
  try:
    with open(config_path, "r") as config_file:
      config = json.load(config_file)
      color = config.get("CONFIGURABLE", {}).get("background_color", "black")

      if color not in acceptable_colors:
        raise ConfigurationError(
          f'{func}; Color "{color}" is not acceptable. Acceptable colors include: {", ".join(acceptable_colors)}'
      )
    return color
  except KeyError as e:
    raise ConfigurationError(f"{func}; Missing expected key in the configuration file: {e}")