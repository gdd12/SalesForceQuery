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
    self.msg = "is connected to the program"
    self.extras = None

  def run(self, type: str, extras=None):
    self.extras = extras

    tool_modules = {
      VARS.Vacation: self.VACATION_TOOL,
      VARS.Exclude:  self.EXCLUSION_TOOL,
      VARS.Clean:    self.CLEAN_TOOL,
      VARS.Config:   self.CONFIG_TOOL,
      VARS.Setup:    self.SETUP_TOOL,
      VARS.Role:     self.ROLE_TOOL,
      VARS.Team:     self.TEAM_TOOL,
    }

    if type == None:
      handle_shutdown(1, reason="Invalid Tool")

    tool_result = tool_modules.get(type, lambda: "unkown")()

  def CLEAN_TOOL(self):
    tool_name = self.CLEAN_TOOL.__name__
    logger.info(f"{tool_name} is connected to the program")

    self.config.clean()
    self.config.remove_key_files()
    self.config.update_config_value("rules.vacation_scheduled_until", value="")

    msg = f"{tool_name} completed the clean operation"
    logger.info(msg)
    handle_shutdown(reason=msg, module=tool_name)

  def VACATION_TOOL(self, date):
    tool_name = self.VACATION_TOOL.__name__
    logger.info(f"{tool_name} is connected to the program")

    if date and type(calculate_days_delta(date)) != int:
      logger.error(f"Unable to set vacation return date {date} as it is invalid.")
      handle_shutdown(module=tool_name)

    result = self.config.update_config_value(key="rules.vacation_scheduled_until", value=date)

    msg = f"{tool_name} completed the vacation setup with the date {result}"
    logger.info(msg)
    handle_shutdown(reason=msg, module=tool_name)
  
  def CONFIG_TOOL(self):
    tool_name = self.CONFIG_TOOL.__name__
    logger.info(f"{tool_name} {self.msg}")
    self.config.print_configuration()

    msg = f"{tool_name} completed the print operation"
    logger.info(msg)
    handle_shutdown(reason=msg, module=tool_name)
  
  def EXCLUSION_TOOL(self):
    tool_name = self.EXCLUSION_TOOL.__name__
    logger.info(f"{tool_name} {self.msg}")

    extras: dict = self.extras

    self.config.add_exclusion(extras)

    msg = f"{tool_name} completed the exclusion of type {str(extras.get('type')).upper()}"
    logger.info(msg)
    handle_shutdown(reason=msg, module=tool_name)
  
  def SETUP_TOOL(self):
    tool_name = self.SETUP_TOOL.__name__
    logger.info(f"{tool_name} {self.msg}")
    rewrite_configuration()

    msg = f"{tool_name} completed",
    logger.info(msg)
    handle_shutdown(reason=msg, module=tool_name)
  
  def SIMULATE_TOOL(self, extras):
    from tools.simulation import simulate

    tool_name = self.SIMULATE_TOOL.__name__
    logger.info(f"{tool_name} {self.msg}")
    simulate(logger=extras)

    msg = f"{tool_name} completed the simulation of the query"
    logger.info(msg)
    handle_shutdown(reason=msg, module=tool_name)
  
  def ROLE_TOOL(self):
    tool_name = self.ROLE_TOOL.__name__
    logger.info(f"{tool_name} {self.msg}")
    new_role = self.config.toggle_role()

    msg = f"{tool_name} completed the switch to {new_role} role"
    logger.info(msg)
    handle_shutdown(reason=msg, module=tool_name)

  def TEAM_TOOL(self):
    tool_name = self.TEAM_TOOL.__name__
    logger.info(f"{tool_name} {self.msg}")

    extra: str = self.extras

    filereg = FileReg()
    filereg.init()

    TeamTool = Team.bootstrap(
      filereg=filereg,
      Add=(str(extra).lower() == "add"),
      Toggle=(str(extra).lower() == "toggle"),
      Remove=(str(extra).lower() == "remove"),
    )
    TeamTool.run()

    msg = f"{tool_name} completed the {extra.upper()} operation"
    logger.info(msg)
    handle_shutdown(reason=msg, module=tool_name)