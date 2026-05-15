import sys
import warnings

from logger import logger
from utils.helper import handle_shutdown, calculate_days_delta
from utils.variables import VARS, FileNames

from config.config import Config, rewrite_configuration
from config.team import Team
from config.filereg import FileReg

class Tools():
  def __init__(self, config_with_filereg):
    self.config: Config = config_with_filereg

  def run(self, type: str, extras=None):
    if type == None: handle_shutdown(1, reason="Invalid Tool")

    elif type == VARS.Vacation: result = self.VACATION_TOOL(extras)
    elif type == VARS.Exclude:  result = self.EXCLUSION_TOOL(extras)
    elif type == VARS.Clean:    result = self.CLEAN_TOOL()
    elif type == VARS.Config:   result = self.CONFIG_TOOL()
    elif type == VARS.Setup:    result = self.SETUP_TOOL()
    elif type == VARS.Role:     result = self.ROLE_TOOL()
    elif type == VARS.Team:     result = self.TEAM_TOOL(extras)
    
    logger.info(result)
    print(result)
    handle_shutdown(exit_code=0)

  def CLEAN_TOOL(self):
    tool_name = self.CLEAN_TOOL.__name__
    logger.info(f"{tool_name} is connected to the program")
    cfg_clean = self.config.clean()
    passwd_clean = self.config.remove_key_files()
    vacation_clean = self.config.update_config_value("rules.vacation_scheduled_until", value="")

    return f"{tool_name} completed the clean operation"

  def VACATION_TOOL(self, date):
    tool_name = self.VACATION_TOOL.__name__
    logger.info(f"{tool_name} is connected to the program")

    if date and type(calculate_days_delta(date)) != int:
      return f"Unable to set vacation return date {date} as it is invalid."

    result = self.config.update_config_value(key="rules.vacation_scheduled_until", value=date)

    return f"{tool_name} completed the vacation setup with the date {result}"
  
  def CONFIG_TOOL(self):
    tool_name = self.CONFIG_TOOL.__name__
    logger.info(f"{tool_name} is connected to the program")
    self.config.print_configuration()

    return f"{tool_name} completed the print operation"
  
  def EXCLUSION_TOOL(self, extras):
    tool_name = self.EXCLUSION_TOOL.__name__
    logger.info(f"{tool_name} is connected to the program")
    self.config.add_exclusion(extras)

    return f"{tool_name} completed the exclusion of {extras}"
  
  def SETUP_TOOL(self):
    tool_name = self.SETUP_TOOL.__name__
    logger.info(f"{tool_name} is connected to the program")
    rewrite_configuration()

    return f"{tool_name} completed"
  
  def SIMULATE_TOOL(self, extras):
    from tools.simulation import simulate

    tool_name = self.SIMULATE_TOOL.__name__
    logger.info(f"{tool_name} is connected to the program")
    simulate(logger=extras)

    return f"{tool_name} completed the simulation of the query"
  
  def ROLE_TOOL(self):
    tool_name = self.ROLE_TOOL.__name__
    logger.info(f"{tool_name} is connected to the program")
    new_role = self.config.toggle_role()

    return f"{tool_name} completed the switch to {new_role} role"

  def TEAM_TOOL(self, extra):
    tool_name = self.TEAM_TOOL.__name__
    logger.info(f"{tool_name} is connected to the program")

    filereg = FileReg()
    filereg.init()

    TeamTool = Team.bootstrap(
      filereg=filereg,
      Print=(extra is True),
      Update=(str(extra).lower() == "add"),
      Viewable=(str(extra).lower() == "view"),
    )
    TeamTool.run()

    return f"{tool_name} completed the {extra.upper()} operation"