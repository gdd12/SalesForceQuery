import warnings
import signal
import sys
import os

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
    self.verbose = False
    self.test = False

    self.ctx = None

    self.setup()
    
  def setup(self):
    user_args = user_defined_args(self.argv)
    args = argument_handler(user_args)

    self.debug = bool(args.get(VARS.Debug, False))
    self.test = bool(args.get(VARS.Test, False))

    log_level = "info"

    if self.debug:
      log_level = "debug"
    
    # Need to check if there is debug enabled through config.json

    setup_logger(log_level)
    self.logger = base_logger

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
      self.logger.error(f"FATAL - Configuration validation failed")
      self.logger.error(f"{type(e).__name__}: {e}")
      print("\nThe above exception(s) may be recoverable by performing a clean operation: main.py -z\n")
      raise

    try:
      self.logger.info("******************* Setup Complete *******************")

      config_data = ctx.config.load_file()
      teamsList = ctx.team.load_teams_list()

      role = config_data[VARS.Role]
      send_notifications = config_data[VARS.Notifications][VARS.SendNotif]

      if (
        not os.path.exists(Path(__file__).resolve().parent.parent / VARS.Config / FileNames.PasswordFile) or
        not os.path.exists(Path(__file__).resolve().parent.parent / VARS.Config / FileNames.KeyFile) or
        not ctx.counter.ok()
      ): generate_encrypted_passwd()

      ctx.handler.run(role, self.debug, send_notifications, config_data, self.test, teamsList)

    except Exception as e:
      self.logger.exception(f"{type(e).__name__}: {e}")
      print(f"{type(e).__name__}: {e}")

def signal_handler(sig, frame):
  handle_shutdown(0)

if __name__ == "__main__":
  AppStartup(sys.argv).run()