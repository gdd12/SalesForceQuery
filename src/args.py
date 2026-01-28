import sys
import warnings
warnings.filterwarnings("ignore")

from logger import logger as base_logger
from helper import handle_shutdown
from variables import Arg_Flag_Alias, Arg_Definition, VARS
from config import add_excluded_cases, rewrite_configuration, load_configuration, load_teams_list, request_password, print_configuration, team_tool, toggle_role

def user_defined_args():
  parsed = {}
  i = 1
  argv = sys.argv

  while i < len(argv):
    arg = argv[i]

    if arg.startswith('-'):
      normalized = arg.lower()

      if normalized not in Arg_Flag_Alias:
        print(f'WARNING - Unknown flag `{arg}`. Valid values can be found through -h')
        handle_shutdown(0, reason="Unknown argument flag")

      key = Arg_Flag_Alias[normalized]
      if key.lower() == 'help':
        print_help()
        break
      value = True

      if i + 1 < len(argv) and not argv[i + 1].startswith('-'):
        value = argv[i + 1]
        i += 1

      parsed[key] = value
    else:
      parsed.setdefault('_positional', []).append(arg)

    i += 1

  return parsed

def print_help():
  print('\nBelow are the flags available for this tool:\n')
  for short, description in Arg_Definition:
    print(f"{'':<2}{short:<3} | {description}")
  handle_shutdown(0)

def argument_handler(arg_obj):
  debug = False
  testMode = False
  verboseMode = False
  forceNotifications = False
  
  base_logger.info(f"Arguments passed in include: {arg_obj}")

  if VARS.Debug in arg_obj: debug = True
  if VARS.Test in arg_obj: testMode = True
  if VARS.Verbose in arg_obj:
    verboseMode = True
    debug = True

  if VARS.Config in arg_obj: print_configuration()
  if VARS.Exclude in arg_obj:
    add_excluded_cases(arg_obj[VARS.Exclude])
    handle_shutdown(0, reason="Must exit to reload configuration")
  if VARS.Setup in arg_obj:
    rewrite_configuration()
  if VARS.Simulate in arg_obj:
    from simulation import simulate
    simulate(base_logger)
  if VARS.Team in arg_obj:
    team_tool(
      Print=(True if type(arg_obj[VARS.Team]) == bool else False),
      Update=(True if str(arg_obj[VARS.Team]).lower() == 'update' else False),
      Viewable=(True if str(arg_obj[VARS.Team]).lower() == 'viewable' else False)
    )
  if VARS.Role in arg_obj:
    toggle_role()

  return {VARS.Debug: debug, VARS.Test: testMode, VARS.Verbose: verboseMode}