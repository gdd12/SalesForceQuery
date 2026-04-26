import json
import os
import shutil
from getpass import getpass
from exceptions import ConfigurationError
import xml.etree.ElementTree as ET
from helper import handle_shutdown
from logger import logger
from variables import VARS, FileNames

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
config_path = os.path.join(base_dir, "config", FileNames.Config)

def load_configuration():
  registry = FileReg()
  registry.read()

  config_template = registry.resolve_file("configTemplate")
  teams_template = registry.resolve_file("teamsTemplate")
  teams_path = registry.resolve_file("teamsPath")
  logger.debug(f"Returned the full path from {FileNames.FileReg} children")

  if not file_exists(config_path): interactive_config_setup(config_path, config_template, CalledFrom='System') 
  if not file_exists(teams_path): register_teams_list(teams_path, teams_template)

  config = load_json_file(config_path, fatal=True)
  logger.info("Configuration set up completed... Continue to main routine.")
  return config

def request_password():
  password = getpass("API Password: ")
  return password

class FileReg():
  def __init__(self):
    base_dir = os.path.dirname(__file__)
    self.os = os.name
    self.fr_location = os.path.abspath(os.path.join(base_dir, "..", "config", FileNames.FileReg))
    self.fr_template = (
      os.path.abspath(os.path.join(base_dir, "..", "templates", FileNames.FileReg)) if self.os != "nt" else
      os.path.abspath(os.path.join(base_dir, "..", "templates", FileNames.FileRegWin))
    )
    self.file_paths = {}
  def validate(self):
    if os.path.exists(self.fr_location):
      return

    logger.debug(f"This is the first startup and {FileNames.FileReg} does not exist. Generating from the templates library.")
    self.generate()

  def generate(self):
    try:
      if not os.path.exists(self.fr_template):
        logger.error(f"{FileNames.FileReg} could not be generated")
        raise FileNotFoundError(self.fr_template)
      shutil.copy(
        self.fr_template,
        self.fr_location
      )
      logger.debug(f"{FileNames.FileReg} has been generated")
    except FileNotFoundError:
      raise

  def read(self):
    try:
      if not os.path.exists(self.fr_location):
        raise FileNotFoundError(self.fr_location)

      tree = ET.parse(self.fr_location)
      root = tree.getroot()
      for file_elem in root.findall("File"):
        name = file_elem.get("name")
        path = file_elem.get("path")
        if not name or not path:
          raise ConfigurationError(f"Missing 'name' or 'path' attribute in one of the <File> entries.")
        self.file_paths[name] = path.strip()

      logger.debug(f"{FileNames.FileReg} has been loaded")
      return self.file_paths
    except FileNotFoundError:
      raise
    except ET.ParseError as e:
      raise ConfigurationError(f"Error parsing XML: {FileNames.FileReg} {e}")
  
  def resolve_file(self, file):
    if not self.file_paths:
      raise KeyError(
        f"FileReg.resolve_file() called before initialization. "
        f"Requested key='{file}', file_paths is empty."
      )
    return os.path.join(base_dir, self.file_paths.get(file))

def load_excluded_cases():
  excludedCasesFile = os.path.join(base_dir, "config", FileNames.ExCases)
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
    logger.warning(f"Excluded file config cannot be found, displaying all returned cases.")
    return set()

def add_excluded_cases(case_name: str):
  excludedCasesFile = os.path.join(base_dir, "config", FileNames.ExCases)
  existing_cases = set()

  if os.path.exists(excludedCasesFile):
    with open(excludedCasesFile, 'r') as file:
      existing_cases = {line.strip() for line in file if line.strip() and not line.strip().startswith('#')}

  if case_name in existing_cases:
    print(f'\nCase {case_name} already exits in {FileNames.ExCases}')
    logger.warning(f'Case {case_name} already exits in {FileNames.ExCases}')
    return

  if case_name.upper() == 'RESET':
    template = '# Any cases you do not want to be notified about can be placed here.'
    try:
      if file_exists(excludedCasesFile):
        os.remove(excludedCasesFile)
      with open(excludedCasesFile, 'w') as file:
        file.write(template + '\n')
      print(f'Successfully reset {FileNames.ExCases}')
      logger.info(f'Successfully reset {FileNames.ExCases}')
    except Exception as e:
      logger.error(f"Failed to reset {excludedCasesFile}: {e}")
    return

  if not case_name.isdigit():
    msg = f"Invalid argument '{case_name}'. Must be an INTEGER. Did you mean to type 'RESET'?"
    logger.warning(msg)
    print(msg)
    handle_shutdown()
  
  try:
    with open(excludedCasesFile, 'a') as file:
      file.write(case_name + '\n')
    logger.info(f"Added '{case_name}' to {excludedCasesFile}.")
    print(f'\nCase {case_name} added to {FileNames.ExCases}')

  except Exception as e:
    logger.error(f"Failed to add '{case_name}' to {excludedCasesFile}: {e}")

def load_excluded_products():
  excludedProductsFile = os.path.join(base_dir, "config", FileNames.ExProducts)
  try:
    with open(excludedProductsFile, 'r') as file:
      lines = file.readlines()
      excluded = {
        line.strip() for line in lines
        if line.strip() and not line.strip().startswith('#')
      }
      logger.debug(f"Total: {len(excluded)}. Excluded products include: {excluded}")
      return excluded
  except FileNotFoundError:
    logger.warning(f"Excluded file config cannot be found, displaying all returned products.")
    return set()
  return

def add_excluded_product(product=None):
  excludedProductsFile = os.path.join(base_dir, "config", FileNames.ExProducts)

  product_to_exclude = product
  if not product:
    product_to_exclude = get_non_empty_input("Enter a product to exclude (RESET to reset the file): ")  

  existing_products = set()

  if os.path.exists(excludedProductsFile):
    with open(excludedProductsFile, 'r') as file:
      existing_products = {line.strip() for line in file if line.strip() and not line.strip().startswith('#')}

  if product_to_exclude in existing_products:
    print(f'\nProduct {product_to_exclude} already exits in {FileNames.ExProducts}')
    logger.warning(f'Product {product_to_exclude} already exits in {FileNames.ExProducts}')
    return

  if product_to_exclude.upper() == 'RESET':
    template = '# Any products you do not support can be placed in this file on new lines'
    try:
      if file_exists(excludedProductsFile):
        os.remove(excludedProductsFile)
      with open(excludedProductsFile, 'w') as file:
        file.write(template + '\n')
      print(f'Successfully reset {FileNames.ExProducts}')
      logger.info(f'Successfully reset {FileNames.ExProducts}')
    except Exception as e:
      logger.error(f"Failed to reset {excludedProductsFile}: {e}")
    return
  try:
    with open(excludedProductsFile, 'a') as file:
      file.write(product_to_exclude + '\n')
    logger.info(f"Added '{product_to_exclude}' to {excludedProductsFile}.")
    print(f'\nProduct {product_to_exclude} added to {FileNames.ExProducts}')

  except Exception as e:
    logger.error(f"Failed to add '{product_to_exclude}' to {excludedProductsFile}: {e}")

def interactive_config_setup(config_path, config_template_path, CalledFrom=None):
  if CalledFrom == 'System':
    print("--- Configuration Setup ---")
    logger.info(f"Config does not exist. Starting interactive setup for {FileNames.Config}")
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

  logger.info(f"Initial configuration completed and saved to {FileNames.Config}")
  print("\nConfiguration saved successfully.\n")

def get_non_empty_input(prompt):
  while True:
    value = input(prompt).strip()
    if value:
      return value
    print("This field cannot be empty.")

def file_exists(path, fatal=False, message=None, Proc=False):
  if not os.path.exists(path):
    if fatal:
      logger.error(message or f"Required file not found: {path}")
      handle_shutdown(1, reason="Missing required file")
    else:
      logger.debug(f"File {path} does not exist, and is not required at this time.")
      return False
  logger.debug(f"File {path} exists")
  return True

def load_json_file(path, fatal=False, context="", Proc=False):
  try:
    if os.path.exists(path):
      with open(path, "r") as f:
        return json.load(f)
  except Exception as e:
    msg = f"Failed to load JSON file at {path}"
    if context:
      msg += f" during {context}"
    logger.error(f"{msg}: {e}")
    if fatal:
      print(f"{msg} {e}")
      handle_shutdown(1, reason=e)
  
def create_json_file(path, data):
  try:
    with open(path, "w") as f:
      json.dump(data, f, indent=2)
    logger.info(f"Successfully wrote {os.path.split(path)[1]} to {path}")
  except Exception as e:
    logger.error(f"Failed to write to {path}: {e}")
    raise

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
  file_registry = FileReg()
  config_path = file_registry.resolve_file("configPath")
  config_template = file_registry.resolve_file("configTemplate")

  interactive_config_setup(config_path, config_template, CalledFrom='User')

def get_config_value(key: str, Proc=False):
  child = ''
  try:
    key_components = key.split(".")
    if len(key_components) > 1:
      child = key_components[1]
    parent = key.split('.')[0]
    config_data = load_json_file(config_path, Proc=Proc, fatal=True)
    if config_data:
      config_value_from_key = config_data.get(parent)

      if child: config_value_from_key = config_data.get(parent).get(child)
      if config_value_from_key == None:
        raise KeyError(f"Invalid key: {key}")

      logger.debug(f"Returning value {config_value_from_key} from {key} ")
      return config_value_from_key
    return
  except KeyError as e:
    raise e

def register_teams_list(teams_path, teams_template):
  with open(teams_template, 'r') as template_file:
    template_data = json.load(template_file)

  with open(teams_path, 'w') as teams_file:
    json.dump(template_data, teams_file, indent=2)

  error_reason = "Teams list is empty, the program cannot run without it. \nRun the program with -t to update. Consult with the help page via the -h arguments for assistance."
  logger.error(error_reason)
  handle_shutdown(0, reason=error_reason)

def load_teams_list():
  file_registry = FileReg()
  file_registry.read()
  teams_file = file_registry.resolve_file("teamsPath")
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

class TeamTool:
  def __init__(self, Print=False, Update=False, Viewable=False):
    self.print_mode = Print
    self.update = Update
    self.viewable = Viewable

    self.file_registry = FileReg()
    self.registers = self.file_registry.read()
    self.teams = load_teams_list()

    if not self.teams:
      handle_shutdown(1, reason="Error: Teams file cannot be found. Please run without flags to rebuild config.")
    self.team_ids = [team.upper() for team in self.teams.keys()]

  def run(self):
    try:
      self._print_teams()
      team_to_update = self._get_valid_team_id()

      if self.update:
        self._handle_update(team_to_update)

      if self.viewable:
        self._handle_viewable_toggle(team_to_update)

      handle_shutdown(0, reason='Team list updated, must exit to reload.')

    except ValueError:
      logger.error("Invalid team ID")
    except Exception as e:
      logger.error("Error updating team list", exc_info=True)
      raise

  def _print_teams(self):
    print('Current team configuration:\n')
    for team, data in self.teams.items():
      if team.upper() != 'GROUP':
        print(
          f"{team.upper()}:\n"
          f" Viewable: {'Y' if data['viewable'] else 'N'}\n"
          f" List: {data['list']}\n"
        )

  def _request_team_id(self):
    if self.update:
      return get_non_empty_input('\nWhich team ID would you like to add a member to? ')
    if self.viewable:
      return get_non_empty_input('\nWhich team ID would you like to toggle visibility? ')
    handle_shutdown(0)

  def _get_valid_team_id(self):
    while True:
      team_id = self._request_team_id().upper()
      if team_id in self.team_ids:
        return team_id.lower()
      print(f"{team_id} not found. Please provide a valid team ID.")

  def _update_team_file(self, updater):
    teams_file = self.file_registry.resolve_file("teamsPath")

    with open(teams_file, "r") as f:
      data = json.load(f)

    updater(data)

    with open(teams_file, "w") as f:
      json.dump(data, f, indent=2)

  def _handle_update(self, team_id):
    current_list = self.teams[team_id]['list']
    print(f"\nCurrent team: {current_list}")

    new_member = get_non_empty_input(
      "\nAdd team member (comma separate multiple members): "
    )
    updated_list = current_list + new_member + ','

    def updater(data):
      data[team_id]['list'] = updated_list

    self._update_team_file(updater)

    print(f"Successfully added {new_member} to the {team_id} team!")

  def _handle_viewable_toggle(self, team_id):
    current_state = self.teams[team_id]['viewable']

    def updater(data):
      data[team_id]['viewable'] = not current_state

    self._update_team_file(updater)

    print(f"Successfully toggled visibility of {team_id} team!")

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
  type = exclusion.get('type')

  if str(type).upper() not in ["PRODUCT", "CASE"]: print("Invalid request, exclusion TYPE must be 'Product' or 'Case'")
  if str(type).upper() == "CASE":
    case_number = exclusion.get('value')
    add_excluded_cases(str(case_number))
  if str(type).upper() == "PRODUCT": add_excluded_product()