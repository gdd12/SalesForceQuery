import json
import os
import shutil
from pathlib import Path
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
  def __init__(self, filereg):
    self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    self.config_dir = os.path.join(self.base_dir, VARS.Config)
    self.config_path = os.path.join(self.config_dir, FileNames.Config)
    self.required_keys = [
      'username',
      'api_url',
      'engineer_name',
      'debug',
      'role',
      'rules.poll_interval',
      'rules.update_threshold',
      'rules.vacation_scheduled',
      'rules.back_from_vacation',
      'rules.upload_to_tse_board',
      'rules.max_buffer_size_bytes',
      'colors.primary',
      'colors.secondary',
      'notifications.send',
      'notifications.sound',
      'queries.Engineer',
      'queries.Engineer_Forwarding',
      'queries.Manager'
    ]
    self.fileregistry = filereg

  def init(self):
    logger.debug(f"Initializing class %s", __class__.__name__)
    self.fileregistry.read()

    config_template = self.fileregistry.resolve_file("configTemplate")    

    if not os.path.exists(self.config_path):
      if not os.path.exists(config_template): raise FileNotFoundError(config_template)
      interactive_config_setup(self.config_path, config_template, CalledFrom='System') 

    self.validate_items(self.load_file())
    logger.info(f"{__class__.__name__} initialized successfully")

  def load_file(self):
    if not os.path.exists(self.config_path):
      raise FileNotFoundError(self.config_path)
    config = load_json_file(self.config_path, fatal=True)
    return config
  
  def validate_items(self, config):
    logger.info(f"Recursively verifying the keys within {FileNames.Config}")
    missing_keys = []
    
    for key in self.required_keys:
      if not self._has_nested_key(config, key):
        missing_keys.append(key)

    if len(missing_keys) > 0:
      raise ConfigurationError(f"Missing required keys: {missing_keys}")

  def _has_nested_key(self, data, path):
    keys = path.split('.')
    current = data
    for key in keys:
      if not isinstance(current, dict):
        return False
      if key not in current:
        return False
      current = current[key]
    return True

  def get_config_value(self, key: str, default=None):
    child = ''
    key_components = key.split(".")
    if len(key_components) > 1:
      child = key_components[1]
    parent = key.split('.')[0]
    config_data = load_json_file(self.config_path, fatal=True)
    if config_data:
      parent_value = config_data.get(parent)
      config_value_from_key = parent_value

      if parent_value is not None and child:
        config_value_from_key = parent_value.get(child)
      if config_value_from_key == None:
        if default:
          logger.debug(f"Using default value: {config_value_from_key} for {key}")
          return default

        raise KeyError(f"Invalid key: {key}")

      logger.debug(f"Returning value {config_value_from_key} from {key} ")
      return config_value_from_key
    return
  
  def print_configuration(self):
    config = self.load_file()

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
  
  @staticmethod
  def add_exclusion(exclusion):
    type = exclusion.get('type')

    if str(type).upper() not in ["PRODUCT", "CASE"]: print("Invalid request, exclusion TYPE must be 'Product' or 'Case'")
    if str(type).upper() == "CASE":
      case_number = exclusion.get('value')
      Cases().add_excluded_cases(str(case_number))
    if str(type).upper() == "PRODUCT": Products().add_excluded_product()
  
  def clean(self):
    self._remove_files(
      FileNames.QueryResults,
      FileNames.FileReg,
    )

  def remove_key_files(self):
    self._remove_files(
      FileNames.KeyFile,
      FileNames.PasswordFile,
      FileNames.Counter,
    )
    logger.info("Key files have been removed successfully")

  def _remove_files(self, *filenames):
    for filename in filenames:
      self._remove(filename)

  def _remove(self, filename):
    path = Path(self.config_dir) / filename
    try:
      path.unlink()
      logger.info(f"Removed {filename} successfully")
    except FileNotFoundError:
      logger.debug(f"{filename} not found, skipping")
    except PermissionError as e:
      logger.warning(f"Permission denied removing {filename}: {e}")
    except OSError as e:
      logger.warning(f"OS error removing {filename}: {e}")

def interactive_config_setup(config_path, config_template_path, CalledFrom=None):
  if CalledFrom == 'System':
    print("--- Configuration Setup ---")
    logger.info(f"Starting interactive setup due to missing {FileNames.Config} file")
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
  handle_shutdown(reason="\nConfiguration saved successfully. Please re-run the program to continue\n")

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
  try:
    file_registry = FileReg()
    file_registry.read()
    config_path = file_registry.resolve_file("configPath")
    config_template = file_registry.resolve_file("configTemplate")

    interactive_config_setup(config_path, config_template, CalledFrom='User')
  except KeyboardInterrupt:
    handle_shutdown(0)
