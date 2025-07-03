import json
import os
import shutil
import sys
from getpass import getpass
from exceptions import ConfigurationError
import xml.etree.ElementTree as ET

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
config_path = os.path.join(base_dir, "config.json")

def load_configuration():
  func = "load_configuration()"
  def log(msg): DEBUG(debug, f"{func}: {msg}") if 'debug' in locals() else print(f"{func}: {msg}")

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

  if not os.path.exists(credentials_path):
    if os.path.exists(credentials_template):
      shutil.copy(credentials_template, credentials_path)
      missing_files.append('credentials.json')
    else:
      raise ConfigurationError(f"{func}; Missing {credentials_path} and no template available.")

  if not os.path.exists(config_path):
    if os.path.exists(config_template):
      shutil.copy(config_template, config_path)
      missing_files.append('config.json')
    else:
      raise ConfigurationError(f"{func}; Missing {config_path} and no template available.")

  if missing_files:
    print(f"[Init Startup] The following configuration files were created from templates: {', '.join(missing_files)}. "
      f"Update and restart.")
    sys.exit(0)

  try:
    with open(config_path, "r") as config_file:
      config = json.load(config_file)

      configurable = config.get("CONFIGURABLE", {})
      queries = config.get("DO_NOT_TOUCH", {}).get("queries", {})

      debug = configurable.get("debug", False)
      log(f"Reading debug value as {debug}")
      log = lambda msg: DEBUG(debug, f"{func}: {msg}")

      supported_products = configurable.get("supported_products", {})
      poll_interval = configurable.get("poll_interval", 5)
      queries = config.get("DO_NOT_TOUCH", {}).get("queries", {})
      send_notifications = configurable.get("notifications", {}).get("send", False)
      sound_notifications = configurable.get("notifications", {}).get("sound", False)
      teams_list = configurable.get("teams_list", {})
      log(f"Read configuration from {config_path}")

      with open(credentials_path, "r") as cred_file:
        salesforce_config = json.load(cred_file)
        log(f"Read Salesforce credentials from {credentials_path}")
      
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
  
def validateFileReg():
  func = "validateFileReg()"
  base_dir = os.path.dirname(__file__)

  if os.name != "nt":
    fileRegSrc = os.path.abspath(os.path.join(base_dir, "..", "templates", "filereg.xml"))
  else:
    fileRegSrc = os.path.abspath(os.path.join(base_dir, "..", "templates", "fileregwin.xml"))

  fileRegDest = os.path.abspath(os.path.join(base_dir, "..", "filereg.xml"))

  if not os.path.exists(fileRegDest):
    print(f"[Init Startup] filereg.xml does not exist in local config, pulling from templates.")
    try:
      if not os.path.exists(fileRegSrc):
        raise FileNotFoundError(f"Template file not found at {fileRegSrc}")

      shutil.copy(fileRegSrc, fileRegDest)
      print(f"[Init Startup] Created filereg.xml based on <{os.name}> Operating System.")
    except FileNotFoundError as e:
      print(f"[Init Startup] ERROR: {e}")
      raise

def readFileReg():
  func = "readFileReg()"

  base_dir = os.path.dirname(__file__)
  file_path = os.path.abspath(os.path.join(base_dir, "..", "filereg.xml"))

  if not os.path.exists(file_path):
    raise FileExistsError(f"{func}; 'filereg.xml' not found at {file_path}")

  try:
    tree = ET.parse(file_path)
    root = tree.getroot()
    file_paths = {}

    for file_elem in root.findall("File"):
      name = file_elem.get("name")
      path = file_elem.get("path")
      if not name or not path:
        raise ConfigurationError(f"{func}; Missing 'name' or 'path' attribute in one of the <File> entries.")
      file_paths[name] = path.strip()
    return file_paths
  except ET.ParseError as e:
    raise ConfigurationError(f"{func}; Error parsing XML: {e}")