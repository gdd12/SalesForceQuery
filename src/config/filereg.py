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
    return os.path.join(self.base_dir, self.file_paths.get(file))