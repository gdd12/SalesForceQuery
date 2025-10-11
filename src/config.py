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

acceptable_colors = [
  "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
  "bright_black", "bright_red", "bright_green", "bright_yellow", "bright_blue",
  "bright_magenta", "bright_cyan", "bright_white"
]

def load_configuration():
  silent_path = silent_config_path()
  if file_exists(silent_path):
    logger.info("Using silent config override")
    config = load_json_file(silent_path, fatal=True)
    return unpack_config(config)
  logger.info("Silent configuration not found, standard loader starting...")
  validateFileReg()
  registry = readFileReg()

  config_path = resolve_registry_path(registry, "configPath")
  credentials_path = resolve_registry_path(registry, "credentialsPath")
  config_template = resolve_registry_path(registry, "configTemplate")
  credentials_template = resolve_registry_path(registry, "credentialsTemplate")
  logger.info("Returned the full path from filereg.xml children")

  if not file_exists(config_path): interactive_config_setup(config_path, config_template)
  if not file_exists(credentials_path): interactive_credentials_setup(credentials_path, credentials_template)

  config = load_json_file(config_path, fatal=True)
  credentials = load_json_file(credentials_path, fatal=True)

  extracted = extract_and_validate_config(config)
  extracted["salesforce_config"] = credentials

  create_silent_file(silent_path, extracted)
  logger.info("Completed... Continue to main routine")
  return unpack_config(extracted)

def request_password():
  password = getpass("Password required for API: ")
  return password

def background_color():
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
    logger.info(f"This is the first startup and filereg.xml does not exist. Pulling from the templates library.")
    try:
      if not os.path.exists(fileRegSrc):
        logger.error(f"filereg.xml cannot be found in the templates library. Exiting.")
        handle_shutdown(1)
      shutil.copy(fileRegSrc, fileRegDest)
      logger.info(f"filereg.xml has been pulled from the templates library")
    except FileNotFoundError as e:
      print(f"[Init Startup] ERROR: {e}")
      raise

def readFileReg():
  base_dir = os.path.dirname(__file__)
  file_path = os.path.abspath(os.path.join(base_dir, "..", "config", "filereg.xml"))

  if not os.path.exists(file_path):
    raise FileExistsError(f"filereg.xml not found at {file_path}")

  try:
    logger.info("Reading filereg.xml")
    tree = ET.parse(file_path)
    root = tree.getroot()
    file_paths = {}

    for file_elem in root.findall("File"):
      name = file_elem.get("name")
      path = file_elem.get("path")
      if not name or not path:
        raise ConfigurationError(f"Missing 'name' or 'path' attribute in one of the <File> entries.")
      file_paths[name] = path.strip()

    logger.info(f"The following paths are initialized: {file_paths}")
    return file_paths
  except ET.ParseError as e:
    raise ConfigurationError(f"Error parsing XML: {e}")

def silent_config_path():
  return os.path.join(base_dir, "config", "silentConfig.json")

def load_excluded_cases():
  excludedCasesFile = os.path.join(base_dir, "config", "excludedCases.cfg")
  try:
    with open(excludedCasesFile, 'r') as file:
      lines = file.readlines()
      excluded = {
        line.strip() for line in lines
        if line.strip() and not line.strip().startswith('#')
      }
      logger.info(f"Loaded {len(excluded)} excluded cases from {excludedCasesFile}")
      return excluded
  except FileNotFoundError:
    logger.info(f"Excluded file config cannot be found, displaying all returned cases.")
    return set()

def add_excluded_cases(case_name: str):
  excludedCasesFile = os.path.join(base_dir, "config", "excludedCases.cfg")
  existing_cases = set()

  if os.path.exists(excludedCasesFile):
    with open(excludedCasesFile, 'r') as file:
      existing_cases = {line.strip() for line in file if line.strip() and not line.strip().startswith('#')}

  if case_name in existing_cases:
    logger.warning(f'Case {case_name} already exits in excludedCases.cfg')
    return

  # Add a reset mechanism for the excludedCases
  if case_name.upper() == 'RESET':
    template = '# Any cases you do not want to be notified about can be placed here.'
    try:
      if file_exists(excludedCasesFile):
        os.remove(excludedCasesFile)
      with open(excludedCasesFile, 'w') as file:
        file.write(template + '\n')
      logger.warning('Successfully reset excludedCases.cfg')
    except Exception as e:
      logger.error(f"Failed to reset {excludedCasesFile}: {e}")
    return

  if not case_name.isdigit():
    logger.warning(f"Invalid argument '{case_name}'. Must be an INTEGER. Did you mean to type 'RESET'?")
    return
  
  try:
    with open(excludedCasesFile, 'a') as file:
      file.write(case_name + '\n')
    logger.info(f"Added '{case_name}' to {excludedCasesFile}.")
    print(f'\nCase {case_name} added to excludedCases.cfg')

  except Exception as e:
    logger.error(f"Failed to add '{case_name}' to {excludedCasesFile}: {e}")

def interactive_config_setup(config_path, config_template_path):
  logger.info("Config does not exist. Starting interactive setup for config.json")
  print("--- Configuration Setup ---")

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

  while True:
    role_response = input("Are you an Engineer or Manager: ").strip().lower()
    if role_response not in ("engineer", "manager"):
      print("Please enter either 'Engineer' or 'Manager'")
    else: break

  config["CONFIGURABLE"]["role"] = role_response

  if not supported_products:
    raise ConfigurationError("No 'supported_products' found in the config template.")

  if role_response == 'engineer':
    while True:
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
      if any(updated_products.values()):
        break
      else:
        print("\nError: At least one product must be enabled.")
  else:
    updated_products = {product: True for product in supported_products}

  config["CONFIGURABLE"].setdefault("supported_products", {})
  config["CONFIGURABLE"]["supported_products"].update(updated_products)
  
  response_notifications = input(f"Enable notifications? [y/n]: ").strip().lower()
  send_notifications = response_notifications in ("y", "yes")

  config["CONFIGURABLE"].setdefault("notifications", {})
  config["CONFIGURABLE"]["notifications"]["send"] = send_notifications

  with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

  logger.info("Initial configuration completed and saved to config.json.")
  print("\nConfiguration saved successfully.\n")

def interactive_credentials_setup(credentials_path, credentials_template):
  logger.info("Credentials does not exist. Starting interactive setup for credentials.json")
  print("\n--- Credentials Setup ---")

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

def file_exists(path, fatal=False, message=None):
  if not os.path.exists(path):
    if fatal:
      logger.error(message or f"Required file not found: {path}")
      handle_shutdown(1)
    else:
      return False
  return True

def load_json_file(path, fatal=False, context=""):
  try:
    with open(path, "r") as f:
      logger.info(f"Loading data from {os.path.split(path)[1]}")
      return json.load(f)
  except Exception as e:
    msg = f"Failed to load JSON file at {path}"
    if context:
      msg += f" during {context}"
    logger.error(f"{msg}: {e}")
    if fatal:
      handle_shutdown(1)
    return None
  
def create_silent_file(path, data):
  try:
    with open(path, "w") as f:
      json.dump(data, f, indent=2)
    logger.info(f"Successfully wrote {os.path.split(path)[1]} to {path}")
  except Exception as e:
    logger.error(f"Failed to write to {path}: {e}")
    raise

def resolve_registry_path(registry, key, default=None):
  return os.path.join(base_dir, registry.get(key, default or key))

def prompt_yes_no(prompt, default=False):
  while True:
    response = input(f"{prompt} [y/n]: ").strip().lower()
    if response in ("y", "yes"):
      return True
    if response in ("n", "no"):
      return False
    if response == "" and default is not None:
      return default

def extract_and_validate_config(config):
  configurable = config.get("CONFIGURABLE", {})
  queries = config.get("DO_NOT_TOUCH", {}).get("queries", {})

  supported_products = {
    k: v for k, v in configurable.get("supported_products", {}).items() if v
  }
  if not supported_products:
    raise ConfigurationError("At least one product must be enabled.")
  logger.info("Extracted and validated the data")
  return {
    "supported_products": supported_products,
    "poll_interval": configurable.get("poll_interval"),
    "queries": queries,
    "debug": configurable.get("debug", False),
    "send_notifications": configurable.get("notifications", {}).get("send", False),
    "sound_notifications": configurable.get("notifications", {}).get("sound"),
    "teams_list": configurable.get("teams_list", {}),
    "role": configurable.get("role"),
    "background_color": configurable.get("background_color", "black"),
    "update_threshold": configurable.get("update_threshold"),
  }

def unpack_config(config_dict):
  try:
    return (
      config_dict["salesforce_config"],
      config_dict["supported_products"],
      config_dict["poll_interval"],
      config_dict["queries"],
      config_dict["debug"],
      config_dict["send_notifications"],
      config_dict["teams_list"],
      config_dict["sound_notifications"],
      config_dict["role"],
      config_dict["background_color"],
      config_dict["update_threshold"]
    )
  except Exception as e:
    logger.error(f"Silent config tainted! Delete {silent_config_path()} and restart.")
    raise(ConfigurationError(f"Missing {e}"))


def rewrite_configuration():
  valid_files = ["config", "creds", "both"]
  print("\n--- Re-writing configuration ---")
  def ask_for_file():
    return input("Rewrite config.json or credentials.json? [config/creds/both]: ").strip().lower()

  while True:
    rewrite_file = ask_for_file()
    if rewrite_file in valid_files:
      break
    else:
      print("Invalid input. Please enter 'config', 'creds', or 'both'.")
  
  file_registry = readFileReg()
  config_path = resolve_registry_path(file_registry, "configPath")
  credentials_path = resolve_registry_path(file_registry, "credentialsPath")
  config_template = resolve_registry_path(file_registry, "configTemplate")
  credentials_template = resolve_registry_path(file_registry, "credentialsTemplate")

  if rewrite_file == "config":
    interactive_config_setup(config_path, config_template)
  elif rewrite_file == "creds":
    interactive_credentials_setup(credentials_path, credentials_template)
  elif rewrite_file == "both":
    interactive_config_setup(config_path, config_template)
    interactive_credentials_setup(credentials_path, credentials_template)
  
  if file_exists(silent_config_path()):
    try:
      os.remove(silent_config_path())
      logger.info(f"Removed silent configuration at {silent_config_path()}")
    except Exception as e:
      logger.error(f"Failed to remove silent configuration: {e}")