import json, os
from utils.helper import handle_shutdown, get_non_empty_input, concat_support_engineer_list
from logger import logger
from utils.variables import VARS, FileNames
from config.filereg import FileReg
from config.config import load_json_file
import exceptions

class Team:
  def __init__(self, filereg, Print=False, Update=False, Viewable=False):
    self.print_mode = Print
    self.update = Update
    self.viewable = Viewable

    self.fileregistry = filereg
    self.registers = None
    self.teams = None
    self.team_ids = []

  @classmethod
  def bootstrap(cls, filereg, Print=False, Update=False, Viewable=False):
    logger.info("Bootstrapping the Team module for argument handling")
    obj = cls(filereg=filereg, Print=Print, Update=Update, Viewable=Viewable)
    obj.init(misconfigured=False)
    return obj
  
  def init(self, misconfigured=True):
    logger.debug(f"Initializing class %s", __class__.__name__)

    teams_template = self.fileregistry.resolve_file("teamsTemplate")
    teams_path = self.fileregistry.resolve_file("teamsPath")

    if not os.path.exists(teams_path):
      if not os.path.exists(teams_template):
          raise FileNotFoundError(teams_template)

      self.register_teams_list(teams_path, teams_template)

    self.teams = self.load_teams_list()

    self.validate_teams_list(self.teams, exit_if_misconfigured=misconfigured)

    self.team_ids = [t.upper() for t in self.teams.keys()]
    logger.info(f"{__class__.__name__} initialized successfully")

  def run(self):
    try:
      self._print_teams()
      team_to_update = self._get_valid_team_id()

      if self.update:
        self._handle_update(team_to_update)

      if self.viewable:
        self._handle_viewable_toggle(team_to_update)

      logger.info('Team list updated, system must exit to reload.')

    except ValueError:
      logger.error("Invalid team ID")
    except Exception as e:
      logger.error("Error updating team list", exc_info=True)
      raise

  def _print_teams(self):
    print('Current team configuration:\n')
    for team, data in self.teams.items():
      if team.upper() != 'GROUP':
        print(
          f"{team.upper()}:\n"
          f" Viewable: {'Y' if data['viewable'] else 'N'}\n"
          f" List: {data['list']}\n"
        )

  def _request_team_id(self):
    if self.update:
      return get_non_empty_input('\nWhich team ID would you like to add a member to? ')
    if self.viewable:
      return get_non_empty_input('\nWhich team ID would you like to toggle visibility? ')
    handle_shutdown(0)

  def _get_valid_team_id(self):
    while True:
      team_id = self._request_team_id().upper()
      if team_id in self.team_ids:
        return team_id.lower()
      print(f"{team_id} not found. Please provide a valid team ID.")

  def _update_team_file(self, updater):
    teams_file = self.fileregistry.resolve_file("teamsPath")

    with open(teams_file, "r") as f:
      data = json.load(f)

    updater(data)

    with open(teams_file, "w") as f:
      json.dump(data, f, indent=2)

  def _handle_update(self, team_id):
    current_list = self.teams[team_id]['list']
    print(f"\nCurrent team: {current_list}")

    new_member = get_non_empty_input(
      "\nAdd team member (comma separate multiple members): "
    )
    updated_list = current_list + new_member + ','

    def updater(data):
      data[team_id]['list'] = updated_list

    self._update_team_file(updater)

    print(f"Successfully added {new_member} to the {team_id} team!")

  def _handle_viewable_toggle(self, team_id):
    current_state = self.teams[team_id]['viewable']

    def updater(data):
      data[team_id]['viewable'] = not current_state

    self._update_team_file(updater)

    print(f"Successfully toggled visibility of {team_id} team!")
  
  def register_teams_list(self, teams_path, teams_template):
    logger.info("Registering the teams list from the template")
    with open(teams_template, 'r') as template_file:
      template_data = json.load(template_file)

    with open(teams_path, 'w') as teams_file:
      json.dump(template_data, teams_file, indent=2)

    error_reason = "Teams list is empty, the program cannot run without it. \nRun the program with -t to update. Consult with the help page via the -h arguments for assistance."
    handle_shutdown(0, reason=error_reason)

  def load_teams_list(self):
    teams_file = self.fileregistry.resolve_file("teamsPath")
    return load_json_file(teams_file, fatal=True)

  @staticmethod
  def validate_teams_list(teams_list, exit_if_misconfigured=True):
    try:
      other_names = []
      for k, v in teams_list.items():
        if k != "group":
          names = v["list"].split(",") if v["viewable"] else []
          other_names.extend(names)

      if (other_names) == '':
        logger.warning(f"Team list is empty, query may return no results")

      quoted_names = [f"'{name.strip()}'" for name in other_names]
      if len(quoted_names) < 1 and exit_if_misconfigured:
        failure_reason = f"No 'Viewable' team list configured. Please utilize the '-t view' flag to update or manually update the {FileNames.Teams}"
        raise exceptions.MalformedTeamConfiguration(failure_reason)
      logger.debug(f"TSE list has undergone formating for SQL query")
      return ", ".join(quoted_names)
    except Exception as e:
      raise