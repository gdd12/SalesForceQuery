import sys
import warnings

warnings.filterwarnings("ignore")

from logger import logger as base_logger
from utils.helper import handle_shutdown
from utils.variables import VARS, FileNames
from config.config import Config, rewrite_configuration, TeamTool

def user_defined_args(args):
  arg_obj = {
    VARS.Config: False,
    VARS.Debug: False,
    VARS.Verbose: False,
    VARS.Test: False,
    VARS.Setup: False,
    VARS.Team: False,
    VARS.Simulate: False,
    VARS.Role: False,
    VARS.Exclude: False,
    VARS.Clean: False
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

    elif arg.lower() in ["-dv", "-vd"]:
      arg_obj[VARS.Debug] = True
      arg_obj[VARS.Verbose] = True

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
  verboseMode = False
  forceNotifications = False

  base_logger.info(f"Arguments passed in include: {arg_obj}")

  if arg_obj[VARS.Debug]:
    debug = True

  if arg_obj[VARS.Clean]:
    Config().clean()
    handle_shutdown(0, reason="Clean completed")
  if arg_obj[VARS.Test]:
    testMode = True

  if arg_obj[VARS.Verbose]:
    verboseMode = True
    debug = True

  if arg_obj[VARS.Config]:
    Config().print_configuration()

  if arg_obj[VARS.Exclude]:
    Config().add_exclusion(arg_obj[VARS.Exclude])
    handle_shutdown(0, reason="Must exit to reload configuration")

  if arg_obj[VARS.Setup]:
    rewrite_configuration()

  if arg_obj[VARS.Simulate]:
    from tools.simulation import simulate
    simulate(base_logger)
    handle_shutdown(0, reason="Simulation completed")

  if arg_obj[VARS.Team]:
    TeamTool(
      Print=(True if type(arg_obj[VARS.Team]) == bool else False),
      Update=(True if str(arg_obj[VARS.Team]).lower() == 'add' else False),
      Viewable=(True if str(arg_obj[VARS.Team]).lower() == 'view' else False)
    ).run()

  if arg_obj[VARS.Role]:
    Config().toggle_role()

  return {VARS.Debug: debug, VARS.Test: testMode, VARS.Verbose: verboseMode}

def print_help_page():
  print("""
Usage: main.py [any of the below arguments]

Configuration:
  -c                    Print the current config.json configuration
  -r                    Change role
  -t <OPTION>           Edit the teams list ('add' or 'view')
                          Ex: -t view
                          Ex: -t add
  -e <TYPE> <OPT>       Add an exclusion of a case or product. The 'case' option must be followed by a case #.
                        Use the 'RESET' option to reset the file
                          Ex: -e Case 0156872
                          Ex: -e Case RESET
                          Ex: -e Product

Runtime Options:
  -q                    Simulate SQL against SalesForce
  -s                    Interactive config setup
  -x                    Run in test mode, no API call is made ONLY if the ~/config/dataBuffer.json does not exist
  -z                    Clean the system-created config files. Does not remove runtime/user defined data.

Debug Options:
  -d                    Enable logging
  -dv                   Enable verbose logging
""")
  return