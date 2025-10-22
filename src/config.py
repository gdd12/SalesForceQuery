import json
import os
import shutil
from getpass import getpass
from exceptions import ConfigurationError
import xml.etree.ElementTree as ET
from helper import handle_shutdown
from logger import logger

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
config_path = os.path.join(base_dir, "config", "config.json")

def load_configuration():
  validateFileReg()
  registry = readFileReg()

  config_template = resolve_registry_path(registry, "configTemplate")
  teams_template = resolve_registry_path(registry, "teamsTemplate")
  teams_path = resolve_registry_path(registry, "teamsPath")
  logger.debug("Returned the full path from filereg.xml children")

  if not file_exists(config_path): interactive_config_setup(config_path, config_template, CalledFrom='System') 
  if not file_exists(teams_path): register_teams_list(teams_path, teams_template)

  config = load_json_file(config_path, fatal=True)
  logger.info("Configuration set up completed... Continue to main routine.")
  return config

def request_password():
  password = getpass("Password required for API: ")
  return password

def background_color():
  try:
    return get_config_value("background_color")
  except KeyError as e:
    return "black"

def validateFileReg():
  base_dir = os.path.dirname(__file__)
  logger.debug(f"Local machine OS is {os.name}")
  if os.name != "nt":
    fileRegSrc = os.path.abspath(os.path.join(base_dir, "..", "templates", "filereg.xml"))
  else:
    fileRegSrc = os.path.abspath(os.path.join(base_dir, "..", "templates", "fileregwin.xml"))

  logger.debug(f"Location of the template filereg.xml is {fileRegSrc}")

  fileRegDest = os.path.abspath(os.path.join(base_dir, "..", "config", "filereg.xml"))

  if not os.path.exists(fileRegDest):
    logger.debug(f"This is the first startup and filereg.xml does not exist. Pulling from the templates library.")
    try:
      if not os.path.exists(fileRegSrc):
        logger.error(f"filereg.xml cannot be found in the templates library. Exiting.")
        handle_shutdown(1)
      shutil.copy(fileRegSrc, fileRegDest)
      logger.debug(f"filereg.xml has been pulled from the templates library")
    except FileNotFoundError as e:
      print(f"[Init Startup] ERROR: {e}")
      raise

def readFileReg():
  base_dir = os.path.dirname(__file__)
  file_path = os.path.abspath(os.path.join(base_dir, "..", "config", "filereg.xml"))

  if not os.path.exists(file_path):
    raise FileExistsError(f"filereg.xml not found at {file_path}")

  try:
    logger.debug("Reading filereg.xml")
    tree = ET.parse(file_path)
    root = tree.getroot()
    file_paths = {}

    for file_elem in root.findall("File"):
      name = file_elem.get("name")
      path = file_elem.get("path")
      if not name or not path:
        raise ConfigurationError(f"Missing 'name' or 'path' attribute in one of the <File> entries.")
      file_paths[name] = path.strip()

    logger.debug(f"The following paths are initialized: {file_paths}")
    return file_paths
  except ET.ParseError as e:
    raise ConfigurationError(f"Error parsing XML: {e}")

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
      logger.debug(f"Excluded cases include: {excluded}")
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

def interactive_config_setup(config_path, config_template_path, CalledFrom=None):
  if CalledFrom == 'System':
    print("--- Configuration Setup ---")
    logger.info("Config does not exist. Starting interactive setup for config.json")
  if CalledFrom == 'User': print("\n--- Re-writing configuration ---")

  if os.path.exists(config_path):
    with open(config_path, "r") as f:
      config = json.load(f)
  elif os.path.exists(config_template_path):
    with open(config_template_path, "r") as f:
      config = json.load(f)
  else:
    raise ConfigurationError("No configuration file or template available for setup.")

  products = config.get("products", {})
  send_notifications = config.get("notifications", {}).get("send", False)

  while True:
    role_response = input("Are you an Engineer or Manager: ").strip().lower()
    if role_response not in ("engineer", "manager"):
      print("Please enter either 'Engineer' or 'Manager'")
    else: break

  config["role"] = role_response

  if not products:
    raise ConfigurationError("No 'products' found in the config template.")

  if role_response == 'engineer':
    while True:
      print("\nPlease answer with 'y' or 'n' to enable or disable each supported product (default is NO):\n")
      updated_products = {}
      for product, enabled in products.items():
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
    updated_products = {product: True for product in products}

  config.setdefault("products", {})
  config["products"].update(updated_products)

  response_notifications = input(f"Enable notifications? [y/n]: ").strip().lower()
  send_notifications = response_notifications in ("y", "yes")

  config.setdefault("notifications", {})
  config["notifications"]["send"] = send_notifications
  config["api_url"] = get_non_empty_input("Enter the API URL: ")
  config["username"] = get_non_empty_input("Enter your email: ")
  config["engineer_name"] = get_non_empty_input("Enter your full name: ")

  with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

  logger.info("Initial configuration completed and saved to config.json.")
  print("\nConfiguration saved successfully.\n")

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
      logger.debug(f"File {path} does not exist, and is not required at this time.")
      return False
  logger.debug(f"File {path} exists")
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
      print(f"{msg} {e}")
      handle_shutdown(1)
    return None
  
def create_json_file(path, data):
  try:
    with open(path, "w") as f:
      json.dump(data, f, indent=2)
    logger.info(f"Successfully wrote {os.path.split(path)[1]} to {path}")
  except Exception as e:
    logger.error(f"Failed to write to {path}: {e}")
    raise

def resolve_registry_path(registry, key, default=None):
  logger.info(f"Resolving {key}")
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

def rewrite_configuration():
  file_registry = readFileReg()
  config_path = resolve_registry_path(file_registry, "configPath")
  config_template = resolve_registry_path(file_registry, "configTemplate")

  interactive_config_setup(config_path, config_template, CalledFrom='User')

def get_config_value(key: str):
  try:
    config_data = load_json_file(config_path)
    config_value_from_key = config_data.get(key)

    if config_value_from_key == None:
      raise ConfigurationError(f"Invalid key: {key}")

    logger.debug(f"Returning value {config_value_from_key} from {key} ")
    return config_value_from_key
  except ConfigurationError as e:
    raise e

def register_teams_list(teams_path, teams_template):
  with open(teams_template, 'r') as template_file:
    template_data = json.load(template_file)

  with open(teams_path, 'w') as teams_file:
    json.dump(template_data, teams_file, indent=2)

  error_reason = "Teams list was created successfully, however the system cannot run without manually editing/importing valid values."
  logger.error(error_reason)
  print(error_reason)
  handle_shutdown(0)

def load_teams_list():
  registry = readFileReg()
  teams_file = resolve_registry_path(registry, "teamsPath")
  teams = load_json_file(teams_file, fatal=True)
  return teams

def print_or_edit_team_list(Print=False, Update=False, Team=None, Viewable=False):
  logger.info(
    f"{'Printing' if Print else 'Updating'} "
    f"{'team' if Team else 'teams.json configuration'}"
    f"{f' {Team}' if Team else ''}"
  )
  try:
    teams = load_teams_list()

    if Print:
      for team, data in teams.items():
        print(f"{team.upper()}: {data['list']}")
    if Update:
      if not Team:
        return print(f"Error: 'update' requires one positional argument. Example: -team update b2b")

      list_to_update = teams[Team]['list']
      print(f"Current team: {list_to_update}")
      new_member = get_non_empty_input("Add team member: ")
      updated_list = list_to_update + ',' + new_member
    
      registry = readFileReg()
      teams_file = resolve_registry_path(registry, "teamsPath")

      with open(teams_file, "r") as f:
        team_file_data = json.load(f)

      team_file_data[Team]['list'] = updated_list
      
      if Viewable:
        team_file_data[Team]['viewable'] = Viewable

      with open(teams_file, "w") as f:
        json.dump(team_file_data, f, indent=2)
      
      print(f"Succesfully added {new_member} to the {Team} team!")
      if Viewable:
        print(f"Successfully set 'viewable' to true for {Team}")

  except Exception as e:
    logger.error("Error updating team list", exc_info=True)
    raise Exception(e)

def set_viewable_team():
  return