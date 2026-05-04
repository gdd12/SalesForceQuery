import os
from utils.variables import FileNames
from utils.helper import logger, handle_shutdown

class Cases():
  def __init__(self):
    self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

  def load_excluded_cases(self):
    excludedCasesFile = os.path.join(self.base_dir, "config", FileNames.ExCases)
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

  def add_excluded_cases(self, case_name: str):
    excludedCasesFile = os.path.join(self.base_dir, "config", FileNames.ExCases)
    existing_cases = set()

    if os.path.exists(excludedCasesFile):
      with open(excludedCasesFile, 'r') as file:
        existing_cases = {line.strip() for line in file if line.strip() and not line.strip().startswith('#')}

    if case_name in existing_cases:
      logger.warning(f'Case {case_name} already exists in {FileNames.ExCases}')
      return

    if case_name.upper() == 'RESET':
      template = '# Any cases you do not want to be notified about can be placed here.'
      try:
        if os.path.exists(excludedCasesFile):
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
      print(f'Case {case_name} added to {FileNames.ExCases}')

    except Exception as e:
      logger.error(f"Failed to add '{case_name}' to {excludedCasesFile}: {e}")