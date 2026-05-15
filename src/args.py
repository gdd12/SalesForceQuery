import sys
import warnings

warnings.filterwarnings("ignore")

from logger import logger as base_logger
from utils.helper import handle_shutdown, print_help_page
from utils.variables import VARS, FileNames
from config.config import Config, rewrite_configuration
from config.team import Team
from config.filereg import FileReg
from tools.tools import Tools

def user_defined_args(args):
  arg_obj = {
    VARS.Config: False,
    VARS.Debug: False,
    VARS.Test: False,
    VARS.Setup: False,
    VARS.Team: False,
    VARS.Simulate: False,
    VARS.Role: False,
    VARS.Exclude: False,
    VARS.Clean: False,
    VARS.Vacation: False
  }
  if "-H" in args or "-h" in args:
    print_help_page()
    handle_shutdown()
  for idx, arg in enumerate(args[1:]):
    arg = arg.strip()
    if '-' not in arg: continue

    if arg in ["-C", "-c"]:
      arg_obj[VARS.Config] = True

    elif arg in ["-R", "-r"]:
      arg_obj[VARS.Role] = True
    
    elif arg in ["-D", "-d"]:
      arg_obj[VARS.Debug] = True
    
    elif arg in ["-V", "-v"]:
      if idx + 2 >= len(args[1:]):
        handle_shutdown(1, reason="Error: '-v' must be followed by a Month (str) and Day (int)")

      month_arg = str(args[idx + 2])
      day_arg = str(args[idx + 3])
      arg_obj[VARS.Vacation] = f"{month_arg} {day_arg}"

    elif arg in ["-X", "-x"]:
      arg_obj[VARS.Test] = True
    
    elif arg in ["-S", "-s"]:
      arg_obj[VARS.Setup] = True
    
    elif arg in ["-Q", "-q"]:
      arg_obj[VARS.Simulate] = True
    
    elif arg in ["-T", "-t"]:
      if idx + 2 >= len(args):
        arg_obj[VARS.Team] = True
      else:
        val = args[idx + 2].lower()
        if val == 'add':
          arg_obj[VARS.Team] = 'add'
        elif val == 'view':
          arg_obj[VARS.Team] = 'view'
        else:
          arg_obj[VARS.Team] = True

    elif arg in ["-E", "-e"]:
      if idx + 1 >= len(args[1:]):
        handle_shutdown(1, reason="Error: '-e' must be followed by 'case' or 'product'!")

      next_arg = str(args[idx + 2]).lower()

      if next_arg == "product":
        arg_obj[VARS.Exclude] = {"type": "product"}

      elif next_arg == "case":
        case_value_idx = idx + 3
        if case_value_idx >= len(args):          
          handle_shutdown(1, reason="Error: '-e case' must be followed by a case number or 'RESET'!")

        case_value = args[case_value_idx]

        arg_obj[VARS.Exclude] = {
          "type": "case",
          "value": case_value
        }

      else:
        handle_shutdown(1, reason=f"Error: Invalid exclusion type '{next_arg}'. Must be 'Case' or 'Product'")
    
    elif arg in ["-Z", "-z"]:
      arg_obj[VARS.Clean] = True

    else:
      print_help_page()
      handle_shutdown(1, reason=f"Unknown argument: {arg}")
  return arg_obj

def argument_handler(arg_obj):
  debug = False
  testMode = False
  tool_class = Tools(Config(FileReg()))

  if arg_obj[VARS.Debug]: debug = True
  if arg_obj[VARS.Test]:  testMode = True

  if arg_obj[VARS.Vacation]: tool_class.run(type=VARS.Vacation, extras=arg_obj[VARS.Vacation])
  if arg_obj[VARS.Simulate]: tool_class.run(type=VARS.Simulate, extras=base_logger)
  if arg_obj[VARS.Exclude]:  tool_class.run(type=VARS.Exclude, extras=arg_obj[VARS.Exclude])
  if arg_obj[VARS.Config]:   tool_class.run(type=VARS.Config, extras=None)
  if arg_obj[VARS.Clean]:    tool_class.run(type=VARS.Clean, extras=None)
  if arg_obj[VARS.Setup]:    tool_class.run(type=VARS.Setup, extras=None)
  if arg_obj[VARS.Role]:     tool_class.run(type=VARS.Role, extras=None)
  if arg_obj[VARS.Team]:     tool_class.run(type=VARS.Team, extras=arg_obj[VARS.Team])

  base_logger.info(f"Arguments passed in include: {arg_obj}")

  return {VARS.Debug: debug, VARS.Test: testMode}