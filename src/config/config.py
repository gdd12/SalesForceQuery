import json
import os
import shutil
from getpass import getpass
from exceptions import ConfigurationError
import xml.etree.ElementTree as ET
from utils.helper import handle_shutdown, get_non_empty_input
from logger import logger
from utils.variables import VARS, FileNames
from config.cases import Cases
from config.products import Products
from config.filereg import FileReg

class Config():
  def __init__(self):
    self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    self.config_path = os.path.join(self.base_dir, "config", FileNames.Config)

  def load(self):
    registry = FileReg()
    registry.read()

    config_template = registry.resolve_file("configTemplate")
    teams_template = registry.resolve_file("teamsTemplate")
    teams_path = registry.resolve_file("teamsPath")
    logger.debug(f"Returned the full path from {FileNames.FileReg} children")

    if not os.path.exists(self.config_path): interactive_config_setup(self.config_path, config_template, CalledFrom='System') 
    if not os.path.exists(teams_path): register_teams_list(teams_path, teams_template)

    config = load_json_file(self.config_path, fatal=True)
    logger.info("Configuration set up completed... Continue to main routine.")
    return config

  def get_config_value(self, key: str, Proc=False):
    child = ''
    try:
      key_components = key.split(".")
      if len(key_components) > 1:
        child = key_components[1]
      parent = key.split('.')[0]
      config_data = load_json_file(self.config_path, Proc=Proc, fatal=True)
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
  
  def print_configuration(self):
    config = self.load()

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
  
  def toggle_role(self):
    if not os.path.exists(self.config_path): raise FileNotFoundError("Config file not found")
    current_role = self.get_config_value(VARS.Role)
    print(f'Current role: {current_role}')

    while True:
      updated_role = get_non_empty_input("\nNew role (Engineer or Manager): ").lower()
      if updated_role in ('engineer', 'manager'):
        break
      print(f"{updated_role} is not a valid role")

    with open(self.config_path, "r") as f:
      config_data = json.load(f)

    config_data[VARS.Role] = updated_role
    logger.info(f"Updating user role from {current_role} to {updated_role}")

    with open(self.config_path, "w") as f:
      json.dump(config_data, f, indent=2)

    print(f"\nSuccessfully updated the user role to {updated_role}")
    handle_shutdown(0)
  
  def add_exclusion(exclusion):
    type = exclusion.get('type')

    if str(type).upper() not in ["PRODUCT", "CASE"]: print("Invalid request, exclusion TYPE must be 'Product' or 'Case'")
    if str(type).upper() == "CASE":
      case_number = exclusion.get('value')
      Cases().add_excluded_cases(str(case_number))
    if str(type).upper() == "PRODUCT": Products().add_excluded_product()

def request_password():
  password = getpass("API Password: ")
  return password

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
  file_registry.read()
  config_path = file_registry.resolve_file("configPath")
  config_template = file_registry.resolve_file("configTemplate")

  interactive_config_setup(config_path, config_template, CalledFrom='User')

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