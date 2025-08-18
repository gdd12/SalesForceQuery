import json
import os
import shutil
import sys
from getpass import getpass
from exceptions import ConfigurationError
import xml.etree.ElementTree as ET
from helper import handle_shutdown

import logging
logger = logging.getLogger()

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
config_path = os.path.join(base_dir, "config", "config.json")

def load_configuration():
  func = "load_configuration()"
  silent_path = silent_config_path()

  if os.path.exists(silent_path):
    logger.info(f"Silent config file exists at {silent_path} and will be used as an override!")

    logger.warning(f"Warning - A Silent Config file exists. Any future configuration changes must be made to {silent_path}")
    try:
      with open(silent_path, "r") as f:
        logger.info("Loading configuration from silentConfig.json...")
        config = json.load(f)
        return (
          config["salesforce_config"],
          config["supported_products"],
          config["poll_interval"],
          config["queries"],
          config["debug"],
          config["send_notifications"],
          config["teams_list"],
          config["sound_notifications"],
          config["role"],
          config["background_color"],
          config["update_threshold"]
        )
    except Exception as e:
      logger.error(f"Failed to load silentConfig.json: {e}. Falling back to normal configuration process.")

  missing_files = []
  validateFileReg()
  file_registry = readFileReg()

  base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

  def resolve_path(key):
    return os.path.join(base_dir, file_registry.get(key, key))

  config_path = resolve_path("configPath")
  credentials_path = resolve_path("credentialsPath")
  config_template = resolve_path("configTemplate")
  credentials_template = resolve_path("credentialsTemplate")
  logger.info(f"File registry completed")

  if not os.path.exists(credentials_path):
    if os.path.exists(credentials_template):
      interactive_credentials_setup(credentials_path, credentials_template)
    else:
      missing_file = f"Missing {credentials_path} and no template available."
      logger.error(f"{missing_file}")
      raise ConfigurationError(f"{missing_file}")

  if not os.path.exists(config_path) and not os.path.exists(silent_path):
    if os.path.exists(config_template):
      interactive_config_setup(config_path, config_template)
    else:
      missing_file = f"Missing {config_path} and no template available."
      logger.error(f"{missing_file}")
      raise ConfigurationError(f"{missing_file}")

  if missing_files:
    logger.warning("Configuration files were missing on startup, program must exit to reload configuration.\n")
    print(f"Update the following config files and restart the app:")
    for file in missing_files:
      print(f"-> {file}")
    handle_shutdown(exit_code=1)

  try:
    with open(config_path, "r") as config_file:
      config = json.load(config_file)

      configurable = config.get("CONFIGURABLE", {})
      queries = config.get("DO_NOT_TOUCH", {}).get("queries", {})
      debug = configurable.get("debug", False)

      supported_products = configurable.get("supported_products", {})
      supported_products_cleaned = {key: value for key, value in supported_products.items() if value}
      if not supported_products_cleaned:
        logger.error("At least one product must be true in supported_products. Exiting")
        raise ConfigurationError("At least one product must be true in supported_products.")

      poll_interval = configurable.get("poll_interval", 5)
      queries = config.get("DO_NOT_TOUCH", {}).get("queries", {})
      send_notifications = configurable.get("notifications", {}).get("send", False)
      sound_notifications = configurable.get("notifications", {}).get("sound", False)
      teams_list = configurable.get("teams_list", {})
      role = configurable.get("role")
      update_threshold = configurable.get("update_threshold")

      logger.info(f"Configured supported products: {[key for key, value in supported_products.items() if value]}")
      logger.info(f"Polling interval of {poll_interval} minutes is now set")
      logger.info(f"Notifications will{' NOT' if not send_notifications else ''} be sent"f"{f' with sound {sound_notifications.upper()}' if send_notifications else ''}")
      logger.info(f"Role of {role} has been set")
      logger.info(f"Update threshold of {update_threshold} minutes is set")

      with open(credentials_path, "r") as cred_file:
        logger.info("Loading the salesforce configuration URL, engineer name, and username for the API call into memory")
        salesforce_config = json.load(cred_file)
        validated = validateCredentialsFile(salesforce_config)

        if not validated:
          logger.error("Credentials file is not valid. Must exit to prevent issues later.")
          handle_shutdown(0)

      color = background_color()
      logger.info(f"Background color {color.upper()} has been set")

      with open(silent_path, "w") as f:
        json.dump({
          "salesforce_config": salesforce_config,
          "supported_products": supported_products_cleaned,
          "queries": queries,
          "teams_list": teams_list,
          "debug": debug,
          "poll_interval": poll_interval,
          "send_notifications": send_notifications,
          "sound_notifications": sound_notifications,
          "role": role,
          "background_color": color,
          "update_threshold": update_threshold
        }, f, indent=2)

      logger.info("silentConfig.json created successfully for future runs.")
      logger.info(f"Configuration has been loaded successfully and will now return back to the main routine")

      return salesforce_config, supported_products_cleaned, poll_interval, queries, debug, send_notifications, teams_list, sound_notifications, role, color, update_threshold

  except KeyError as e:
    raise ConfigurationError(f"{func}; Missing expected key in the configuration file: {e}")

def request_password():
  logger.info("Requesting password for API")
  password = getpass("Password required for API: ")
  return password

def background_color():
  acceptable_colors = [
    "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
    "bright_black", "bright_red", "bright_green", "bright_yellow", "bright_blue",
    "bright_magenta", "bright_cyan", "bright_white"
  ]
  try:
    silent_config_path = os.path.abspath(
      os.path.join(os.path.dirname(__file__), "..", "config", "silentConfig.json")
    )
    if os.path.exists(silent_config_path):
      with open(silent_config_path, "r") as silent_file:
        config = json.load(silent_file)
        color = config["background_color"]
    else:
      with open(config_path, "r") as config_file:
        config = json.load(config_file)
        color = config.get("CONFIGURABLE", {}).get("background_color", "black")
    return color
  except KeyError as e:
    return "black"

def validateFileReg():
  base_dir = os.path.dirname(__file__)
  logger.info(f"Local machine OS is {os.name}")
  if os.name != "nt":
    fileRegSrc = os.path.abspath(os.path.join(base_dir, "..", "templates", "filereg.xml"))
  else:
    fileRegSrc = os.path.abspath(os.path.join(base_dir, "..", "templates", "fileregwin.xml"))

  logger.info(f"Location of the template filereg.xml is {fileRegSrc}")

  fileRegDest = os.path.abspath(os.path.join(base_dir, "..", "config", "filereg.xml"))

  if not os.path.exists(fileRegDest):
    print(f"[Init Startup] filereg.xml does not exist in local config, pulling from templates.")
    logger.info(f"This is the first startup and filereg.xml does not exist. Pulling from the templates library.")
    try:
      if not os.path.exists(fileRegSrc):
        logger.error(f"filereg.xml cannot be found in the templates library. Exiting.")
        handle_shutdown(1)
      shutil.copy(fileRegSrc, fileRegDest)
      logger.info(f"filereg.xml has been pulled from the templates library")
      print(f"[Init Startup] Created filereg.xml based on <{os.name}> Operating System.")
    except FileNotFoundError as e:
      print(f"[Init Startup] ERROR: {e}")
      raise

def readFileReg():
  base_dir = os.path.dirname(__file__)
  file_path = os.path.abspath(os.path.join(base_dir, "..", "config", "filereg.xml"))

  if not os.path.exists(file_path):
    raise FileExistsError(f"filereg.xml not found at {file_path}")

  try:
    tree = ET.parse(file_path)
    root = tree.getroot()
    file_paths = {}

    for file_elem in root.findall("File"):
      name = file_elem.get("name")
      path = file_elem.get("path")
      if not name or not path:
        raise ConfigurationError(f"Missing 'name' or 'path' attribute in one of the <File> entries.")
      file_paths[name] = path.strip()
      logger.info(f"{name} located at {os.path.abspath(os.path.join(base_dir, '..', path))}")
    return file_paths
  except ET.ParseError as e:
    raise ConfigurationError(f"Error parsing XML: {e}")

def validateCredentialsFile(config):
  required_items = ["url", "engineer_name", "username"]
  missing = [item for item in required_items if not config.get(item)]

  for item in missing:
    logger.error(f"{item.upper()} is empty or missing, and is required!")

  return len(missing) == 0

def silent_config_path():
  return os.path.join(base_dir, "config", "silentConfig.json")

def load_excluded_cases():
  excludedCasesFile = os.path.join(base_dir, "config", "excludedCases.cfg")
  try:
    with open(excludedCasesFile, 'r') as file:
      logger.info(f"Excluded Cases file found at {excludedCasesFile}")
      return {line.strip() for line in file if line.strip() and not line.strip().startswith('#')}
  except FileNotFoundError:
    logger.error(f"The {excludedCasesFile} cannot be found")
    return set()
  
def add_excluded_cases(case_name: str):
  excludedCasesFile = os.path.join(base_dir, "config", "excludedCases.cfg")
  existing_cases = set()
  if os.path.exists(excludedCasesFile):
    with open(excludedCasesFile, 'r') as file:
      existing_cases = {line.strip() for line in file if line.strip() and not line.strip().startswith('#')}

  if case_name in existing_cases:
    logger.info(f"The case '{case_name}' already exists in {excludedCasesFile}.")
    print(f'\nCase {case_name} already exits in excludedCases.cfg')
    return

  try:
    with open(excludedCasesFile, 'a') as file:
      file.write(case_name + '\n')
    logger.info(f"Added '{case_name}' to {excludedCasesFile}.")
    print(f'\nCase {case_name} added to excludedCases.cfg')
  except Exception as e:
      logger.error(f"Failed to add '{case_name}' to {excludedCasesFile}: {e}")

def interactive_config_setup(config_path, config_template_path):
  print("--- Initial Configuration Setup ---")
  logger.info("Starting interactive setup for config.json")

  if os.path.exists(config_path):
    with open(config_path, "r") as f:
      config = json.load(f)
  elif os.path.exists(config_template_path):
    with open(config_template_path, "r") as f:
      config = json.load(f)
  else:
    raise ConfigurationError("No configuration file or template available for setup.")

  configurable = config.get("CONFIGURABLE", {})
  supported_products = configurable.get("supported_products", {})
  send_notifications = configurable.get("notifications", {}).get("send", False)

  if not supported_products:
    raise ConfigurationError("No 'supported_products' found in the config template.")

  print("\nPlease answer with 'y' or 'n' to enable or disable each supported product (default is NO):\n")
  updated_products = {}
  for product, enabled in supported_products.items():
    while True:
      response = input(f"Enable product {product}? [y/n]: ").strip().lower()
      if response in ("y", "yes"):
        updated_products[product] = True
        break
      elif response in ("n", "no", ""):
        updated_products[product] = False
        break

  response_notifications = input(f"Enable notifications? [y/n]: ").strip().lower()
  send_notifications = False
  if response_notifications in ("y", "yes"):
    send_notifications = True

  config["CONFIGURABLE"]["supported_products"] = updated_products
  config["CONFIGURABLE"]["notifications"]["send"] = send_notifications
  with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

  logger.info("Initial configuration completed and saved to config.json.")
  print("\nConfiguration saved successfully.\n")

def interactive_credentials_setup(credentials_path, credentials_template):
  print("\n--- Initial Credentials Setup ---")
  logger.info("Starting interactive setup for credentials.json")

  if os.path.exists(credentials_path):
    with open(credentials_path, "r") as f:
      credentials = json.load(f)
  elif os.path.exists(credentials_template):
    with open(credentials_template, "r") as f:
      credentials = json.load(f)
  else:
    raise ConfigurationError("No configuration file or template available for setup.")

  credentials["url"] = get_non_empty_input("Enter the API URL: ")
  credentials["username"] = get_non_empty_input("Enter your email: ")
  credentials["engineer_name"] = get_non_empty_input("Enter your name: ")

  with open(credentials_path, "w") as f:
    json.dump(credentials, f, indent=2)

  logger.info("Credentials completed and saved to credentials.json.")
  print("\nCredentials saved successfully.\n")

def get_non_empty_input(prompt):
  while True:
    value = input(prompt).strip()
    if value:
      return value
    print("This field cannot be empty.")