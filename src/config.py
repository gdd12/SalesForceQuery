import json
import os
import shutil
from getpass import getpass
from exceptions import ConfigurationError
import xml.etree.ElementTree as ET
from helper import handle_shutdown
from logger import logger, process
from variables import VARS

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
  password = getpass("API Password: ")
  return password

def background_color():
  try:
    return get_config_value("colors")
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
        handle_shutdown(1, reason="Missing required config file")
      shutil.copy(fileRegSrc, fileRegDest)
      logger.debug(f"filereg.xml has been pulled from the templates library")
    except FileNotFoundError as e:
      print(f"[Init Startup] ERROR: {e}")
      raise

def readFileReg(Proc=False):
  active_logger = process if Proc else logger
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
    active_logger.debug("filereg.xml has been loaded")
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
    print(f'\nCase {case_name} already exits in excludedCases.cfg')
    logger.warning(f'Case {case_name} already exits in excludedCases.cfg')
    return

  if case_name.upper() == 'RESET':
    template = '# Any cases you do not want to be notified about can be placed here.'
    try:
      if file_exists(excludedCasesFile):
        os.remove(excludedCasesFile)
      with open(excludedCasesFile, 'w') as file:
        file.write(template + '\n')
      print('Successfully reset excludedCases.cfg')
      logger.info('Successfully reset excludedCases.cfg')
    except Exception as e:
      logger.error(f"Failed to reset {excludedCasesFile}: {e}")
    return

  if not case_name.isdigit():
    msg = f"Invalid argument '{case_name}'. Must be an INTEGER. Did you mean to type 'RESET'?"
    logger.warning(msg)
    print(msg)
    return
  
  try:
    with open(excludedCasesFile, 'a') as file:
      file.write(case_name + '\n')
    logger.info(f"Added '{case_name}' to {excludedCasesFile}.")
    print(f'\nCase {case_name} added to excludedCases.cfg')

  except Exception as e:
    logger.error(f"Failed to add '{case_name}' to {excludedCasesFile}: {e}")

def load_excluded_products():
  excludedProductsFile = os.path.join(base_dir, "config", "excludedProducts.cfg")
  try:
    with open(excludedProductsFile, 'r') as file:
      lines = file.readlines()
      excluded = {
        line.strip() for line in lines
        if line.strip() and not line.strip().startswith('#')
      }
      logger.info(f"Loaded {len(excluded)} excluded products from {excludedProductsFile}")
      logger.debug(f"Excluded products include: {excluded}")
      return excluded
  except FileNotFoundError:
    logger.info(f"Excluded file config cannot be found, displaying all returned products.")
    return set()
  return

def add_excluded_product():
  excludedProductsFile = os.path.join(base_dir, "config", "excludedProducts.cfg")
  product_to_exclude = get_non_empty_input("Enter a product to exclude (RESET to reset the file): ")

  existing_products = set()

  if os.path.exists(excludedProductsFile):
    with open(excludedProductsFile, 'r') as file:
      existing_products = {line.strip() for line in file if line.strip() and not line.strip().startswith('#')}

  if product_to_exclude in existing_products:
    print(f'\nProduct {product_to_exclude} already exits in excludedProducts.cfg')
    logger.warning(f'Product {product_to_exclude} already exits in excludedProducts.cfg')
    return

  if product_to_exclude.upper() == 'RESET':
    template = '# Any products you do not support can be placed in this file on new lines'
    try:
      if file_exists(excludedProductsFile):
        os.remove(excludedProductsFile)
      with open(excludedProductsFile, 'w') as file:
        file.write(template + '\n')
      print('Successfully reset excludedProducts.cfg')
      logger.info('Successfully reset excludedProducts.cfg')
    except Exception as e:
      logger.error(f"Failed to reset {excludedProductsFile}: {e}")
    return
  try:
    with open(excludedProductsFile, 'a') as file:
      file.write(product_to_exclude + '\n')
    logger.info(f"Added '{product_to_exclude}' to {excludedProductsFile}.")
    print(f'\nProduct {product_to_exclude} added to excludedProducts.cfg')

  except Exception as e:
    logger.error(f"Failed to add '{product_to_exclude}' to {excludedProductsFile}: {e}")

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

  send_notifications = config.get("notifications", {}).get("send", False)

  while True:
    role_response = input("Are you an Engineer or Manager: ").strip().lower()
    if role_response not in ("engineer", "manager"):
      print("Please enter either 'Engineer' or 'Manager'")
    else: break

  config["role"] = role_response

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

def file_exists(path, fatal=False, message=None, Proc=False):
  active_logger = process if Proc else logger
  if not os.path.exists(path):
    if fatal:
      active_logger.error(message or f"Required file not found: {path}")
      handle_shutdown(1, reason="Missing required file")
    else:
      active_logger.debug(f"File {path} does not exist, and is not required at this time.")
      return False
  active_logger.debug(f"File {path} exists")
  return True

def load_json_file(path, fatal=False, context="", Proc=False):
  active_logger = process if Proc else logger
  try:
    with open(path, "r") as f:
      return json.load(f)
  except Exception as e:
    msg = f"Failed to load JSON file at {path}"
    if context:
      msg += f" during {context}"
    active_logger.error(f"{msg}: {e}")
    if fatal:
      print(f"{msg} {e}")
      handle_shutdown(1)
  
def create_json_file(path, data):
  try:
    with open(path, "w") as f:
      json.dump(data, f, indent=2)
    logger.info(f"Successfully wrote {os.path.split(path)[1]} to {path}")
  except Exception as e:
    logger.error(f"Failed to write to {path}: {e}")
    raise

def resolve_registry_path(registry, key, default=None, Proc=False):
  active_logger = process if Proc else logger
  active_logger.info(f"Resolving {key}")
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

def get_config_value(key: str, Proc=False):
  active_logger = process if Proc else logger
  child = ''
  try:
    key_components = key.split(".")
    if len(key_components) > 1:
      child = key_components[1]
    parent = key.split('.')[0]
    config_data = load_json_file(config_path, Proc=Proc, fatal=True)
    config_value_from_key = config_data.get(parent)

    if child: config_value_from_key = config_data.get(parent).get(child)
    if config_value_from_key == None:
      raise ConfigurationError(f"Invalid key: {key}")

    active_logger.debug(f"Returning value {config_value_from_key} from {key} ")
    return config_value_from_key
  except ConfigurationError as e:
    raise e

def register_teams_list(teams_path, teams_template):
  with open(teams_template, 'r') as template_file:
    template_data = json.load(template_file)

  with open(teams_path, 'w') as teams_file:
    json.dump(template_data, teams_file, indent=2)

  error_reason = "Teams list is empty, the program cannot run without it. \nRun the program with -t to update!"
  logger.error(error_reason)
  print(error_reason)
  handle_shutdown(0, reason="Team list is not proper, cannot continue")

def load_teams_list():
  registry = readFileReg()
  teams_file = resolve_registry_path(registry, "teamsPath")
  teams = load_json_file(teams_file, fatal=True)
  return teams

def print_configuration():
  config = load_configuration()

  notifications = config[VARS.Notifications]
  colors = config[VARS.Colors]
  rules = config[VARS.Rules]

  logger.info("Printing config to screen")

  print("\n== Current Config ==")
  print(f"  Name: {config[VARS.EngineerName]}")
  print(f"  API: {config[VARS.ApiUrl]}")
  print(f"  Polling Interval: {rules[VARS.Polling]}")
  print(f"  Debug: {config[VARS.Debug]}")
  print(f"  Send Notifications: {notifications[VARS.SendNotif]}")
  print(f"  Notification Sound: {notifications[VARS.SoundNotif]}")
  print(f"  Role: {config[VARS.Role]}")
  print(f"  Colors: {colors[VARS.Primary]} & {colors[VARS.Secondary]}")
  print(f"  Forwarding Engine: {rules['upload_to_tse_board']}")

  handle_shutdown(0)

def team_tool(Print=False, Update=False, Viewable=False):
  try:
    teams = load_teams_list()
    registry = readFileReg()
    team_ids = []

    print('Current team configuration:\n')
    for team, data in teams.items():
      team_ids.append(team.upper())
      if team.upper() != 'GROUP':
        print(
          f"{team.upper()}:\n"
          f" Viewable: {'Y' if data['viewable'] else 'N'}\n"
          f" List: {data['list']}\n"
        )

    def request_team_id_from_user():
      if Update: return get_non_empty_input('\nWhich team ID would you like to update? ')
      if Viewable: return get_non_empty_input('\nWhich team ID would you like to toggle the visibility? ')
      handle_shutdown(0)

    def get_valid_team_id(team_ids):
      while True:
        team_id = request_team_id_from_user().upper()
        if team_id in team_ids:
          return team_id.lower()
        print(f"{team_id} was not found in the team list. Please provide a valid team ID.")

    def update_team_file(registry, updater):
      teams_file = resolve_registry_path(registry, "teamsPath")

      with open(teams_file, "r") as f:
        team_file_data = json.load(f)

      updater(team_file_data)

      with open(teams_file, "w") as f:
        json.dump(team_file_data, f, indent=2)

    team_to_update = get_valid_team_id(team_ids)

    if Update:
      list_to_update = teams[team_to_update]['list']
      print(f"\nCurrent team: {list_to_update}")

      new_member = get_non_empty_input("\nAdd team member: ")
      updated_list = list_to_update + new_member + ','

      def updater(data):
        data[team_to_update]['list'] = updated_list

      update_team_file(registry, updater)
      print(f"Successfully added {new_member} to the {team_to_update} team!")

    if Viewable:
      team_is_viewable = teams[team_to_update]['viewable']

      def updater(data):
        data[team_to_update]['viewable'] = not team_is_viewable

      update_team_file(registry, updater)
      print(f"Successfully toggled visibility of {team_to_update} team!")

    handle_shutdown(0, reason='Team list has been updated, must exit to reload.')

  except Exception as e:
    logger.error("Error updating team list", exc_info=True)
    raise e
  except ValueError as e:
    logger.error("Invalid team ID")

def toggle_role():
  if not file_exists(config_path): raise FileNotFoundError("Config file not found")
  current_role = get_config_value(VARS.Role)
  print(f'Current role: {current_role}')

  while True:
    updated_role = get_non_empty_input("\nNew role (Engineer or Manager): ").lower()
    if updated_role in ('engineer', 'manager'):
      break
    print(f"{updated_role} is not a valid role")

  with open(config_path, "r") as f:
    config_data = json.load(f)

  config_data[VARS.Role] = updated_role
  logger.info(f"Updating user role from {current_role} to {updated_role}")

  with open(config_path, "w") as f:
    json.dump(config_data, f, indent=2)

  print(f"\nSuccessfully updated the user role to {updated_role}")
  handle_shutdown(0)

def add_exclusion(exclusion):
  type = exclusion[0]

  if str(type).upper() not in ["PRODUCT", "CASE"]: print("Invalid request, exclusion TYPE must be 'Product' or 'Case'")
  if str(type).upper() == "CASE": add_excluded_cases(exclusion[1])
  if str(type).upper() == "PRODUCT": add_excluded_product()