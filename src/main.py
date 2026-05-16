import warnings
import signal
import sys
import os
import json

from args import user_defined_args, argument_handler
from logger import setup_logger, logger as base_logger
from utils.variables import VARS, FileNames
from pathlib import Path

from config.config import Config
from config.team import Team
from config.filereg import FileReg
from utils.helper import handle_shutdown
import exceptions as exceptions
from handlers.handler import Handler
from tools.encryption import generate_encrypted_passwd
from tools.counter import Counter
from display.common import CommonDisplay

class AppContext:
  def __init__(self):
    self.filereg = FileReg()
    self.config = Config(self.filereg)
    self.team = Team(self.filereg)
    self.counter = Counter(self.config)
    self.handler = Handler(
      self.config,
      self.filereg,
      self.team,
      self.counter
    )

class AppStartup:
  def __init__(self, argv):
    self.argv = argv
    self.logger = None

    self.debug = False
    self.test = False

    self.ctx = None
    self.config_dir = Path(__file__).resolve().parent.parent / VARS.Config

    self.setup()
    
  def setup(self):
    user_args = user_defined_args(self.argv)
  
    config_debug_flag = False

    config_file_path = self.config_dir / FileNames.Config

    if (config_file_path).exists():
      with open(config_file_path, 'r') as f:
        config_data = json.load(f)
      config_debug_flag = config_data[VARS.Debug]

    self.debug = bool(user_args.get(VARS.Debug, False)) or config_debug_flag
    self.test = bool(user_args.get(VARS.Test, False))

    log_level = "debug" if self.debug else "info"

    setup_logger(log_level)
    self.logger = base_logger

    args = argument_handler(user_args)

    signal.signal(signal.SIGINT, signal_handler)

  def run(self):
    self.logger.info("Logger initialized with debug=%s test=%s", self.debug, self.test)
    CommonDisplay().main_banner()

    ctx = AppContext()

    try:
      self.logger.info("******************** Config Setup ********************")

      ctx.filereg.init()
      ctx.config.init()
      ctx.team.init()
      ctx.counter.init()
      ctx.handler.init()

    except Exception as e:
      self.logger.error(f"FATAL - Configuration validation failed due to the below exception:")
      self.logger.error(f"{type(e).__name__}: {e}")
      if self.debug:
        raise
      handle_shutdown(
        exit_code=1,
        reason='\nThe above exception(s) may be recoverable by performing a clean operation: main.py -z\nThere may be additional information with the -d flag')

    try:
      self.logger.info("******************* Setup Complete *******************")

      cached_buffer_exists = (self.config_dir / FileNames.QueryResults).exists()
      passwd_file_exists = (self.config_dir / FileNames.PasswordFile).exists()
      key_file_exists = (self.config_dir / FileNames.KeyFile).exists()

      counter_ok = ctx.counter.ok()

      test_mode_without_cache = self.test and not cached_buffer_exists

      needs_password_generated = (
        not passwd_file_exists or
        not key_file_exists or
        not counter_ok
      )

      if test_mode_without_cache:
        print(
          f"You are entering Test mode but "
          f"{FileNames.QueryResults} was not previously cached.\n"
          f"Please ensure your password is correctly entered "
          f"as the API will be hit!"
        )
      
      if needs_password_generated or test_mode_without_cache:
        generate_encrypted_passwd()

      config_data = ctx.config.load_file()
      teamsList = ctx.team.load_teams_list()

      role = config_data[VARS.Role]
      send_alerts = config_data[VARS.Alerts][VARS.Send]

      ctx.handler.run(role, self.debug, send_alerts, config_data, self.test, teamsList)

    except Exception as e:
      self.logger.exception(f"{type(e).__name__}: {e}")
      print(f"{type(e).__name__}: {e}")

def signal_handler(sig, frame):
  handle_shutdown(0)

if __name__ == "__main__":
  AppStartup(sys.argv).run()