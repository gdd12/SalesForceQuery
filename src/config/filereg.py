import os, shutil
from utils.variables import FileNames
from logger import logger
from exceptions import ConfigurationError
import xml.etree.ElementTree as ET

class FileReg():
  def __init__(self):
    self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__) , "..", ".."))
    self.os = os.name
    self.fr_location = os.path.abspath(os.path.join(self.base_dir, "config", FileNames.FileReg))
    self.fr_template = (
      os.path.abspath(os.path.join(self.base_dir, "templates", FileNames.FileReg)) if self.os != "nt" else
      os.path.abspath(os.path.join(self.base_dir, "templates", FileNames.FileRegWin))
    )
    self.file_paths = {}

  def init(self):
    logger.debug(f"Initializing class %s", __class__.__name__)
    self.exists()
    self.is_valid()
    self.read()
    logger.info(f"{__class__.__name__} initialized successfully")
    return True

  def exists(self):
    if os.path.exists(self.fr_location):
      return

    logger.debug(f"This is the first startup and {FileNames.FileReg} does not exist. Generating from the templates library.")
    self.generate()

    return os.path.exists(self.fr_location)

  def is_valid(self):
    try:
      tree = ET.parse(self.fr_location)
      root = tree.getroot()

      if root.tag != "Files":
        raise ConfigurationError(f"Invalid root tag '{root.tag}' in {FileNames.FileReg}")

      for file_elem in root.findall("File"):
        name = file_elem.get("name")
        path = file_elem.get("path")

        if not name or not path:
          raise ConfigurationError("Each <File> entry requires 'name' and 'path'")

      return True

    except ET.ParseError as e:
      raise ConfigurationError(f"Malformed XML in {FileNames.FileReg}: {e}")

  def generate(self):
    if not os.path.exists(self.fr_template):
      raise FileNotFoundError(f"A missing template for {FileNames.FileReg} has caused system panic")
    shutil.copy(
      self.fr_template,
      self.fr_location
    )
    logger.debug(f"{FileNames.FileReg} has been generated")

  def read(self):
    try:
      if not os.path.exists(self.fr_location):
        self.generate()

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
      raise RuntimeError("FileReg not initialized. Call init() first.")

    path = self.file_paths.get(file)

    if path is None:
      raise KeyError(f"Unknown file key: '{file}'")

    return os.path.join(self.base_dir, path)