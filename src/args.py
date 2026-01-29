import sys
import warnings
import argparse

warnings.filterwarnings("ignore")

from logger import logger as base_logger
from helper import handle_shutdown
from variables import Arg_Definition, VARS
from config import add_excluded_cases, rewrite_configuration, load_configuration, load_teams_list, request_password, print_configuration, team_tool, toggle_role, add_exclusion

def user_defined_args():
  parser = argparse.ArgumentParser(
    prog="main.py",
    formatter_class=argparse.RawTextHelpFormatter
  )

  config = parser.add_argument_group("Configuration")
  config.add_argument(
    "-c", "--config",
    action="store_true",
    help="Print the current config.json configuration"
  )
  config.add_argument(
    "-r", "--role",
    action="store_true",
    help="Change role"
  )
  config.add_argument(
    "-t", "--team",
    metavar="METHOD",
    help="Edit the teams list (update | viewable)"
  )
  config.add_argument(
    "-e", "--exclude",
    nargs='+',
    metavar=("TYPE", "VALUE"),
    help=(
      "Exclude item by type and value.\n"
      "TYPE must be 'Product' or 'Case'\n"
      "  Ex: -e Product B2Bi\n"
      "  Ex: -e Case 01738532"
    )
  )

  runtime = parser.add_argument_group("Runtime Options")
  runtime.add_argument(
    "-q", "--simulate",
    action="store_true",
    help="Simulate SQL against runtime server"
  )
  runtime.add_argument(
    "-s", "--setup",
    action="store_true",
    help="Interactive config setup"
  )
  runtime.add_argument(
    "-x", "--test",
    action="store_true",
    help="Run in test mode"
  )

  debug = parser.add_argument_group("Debug Options")

  debug.add_argument(
    "-d", "--debug",
    action="store_true",
    help="Enable logging"
  )

  debug.add_argument(
    "-dv", "--debug-verbose",
    action="store_true",
    help="Enable verbose logging"
  )

  args = parser.parse_args()
  return vars(args)

def argument_handler(arg_obj):
  debug = False
  testMode = False
  verboseMode = False
  forceNotifications = False

  base_logger.info(f"Arguments passed in include: {arg_obj}")

  if arg_obj[VARS.Debug]:
    debug = True

  if arg_obj[VARS.Test]:
    testMode = True

  if arg_obj[VARS.Verbose]:
    verboseMode = True
    debug = True

  if arg_obj[VARS.Config]:
    print_configuration()

  if arg_obj[VARS.Exclude]:
    add_exclusion(arg_obj[VARS.Exclude])
    handle_shutdown(0, reason="Must exit to reload configuration")

  if arg_obj[VARS.Setup]:
    rewrite_configuration()

  if arg_obj[VARS.Simulate]:
    from simulation import simulate
    simulate(base_logger)

  if arg_obj[VARS.Team]:
    team_tool(
      Print=(True if type(arg_obj[VARS.Team]) == bool else False),
      Update=(True if str(arg_obj[VARS.Team]).lower() == 'update' else False),
      Viewable=(True if str(arg_obj[VARS.Team]).lower() == 'viewable' else False)
    )

  if arg_obj[VARS.Role]:
    toggle_role()

  return {VARS.Debug: debug, VARS.Test: testMode, VARS.Verbose: verboseMode}