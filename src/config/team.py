import json, os
from utils.helper import handle_shutdown, get_non_empty_input
from logger import logger
from utils.variables import VARS, FileNames
from config.filereg import FileReg
from config.config import load_json_file
import exceptions

class Team:
  def __init__(self, filereg: FileReg,  Add=False, Toggle=False, Remove=False):
    self.toggle = Toggle
    self.add = Add
    self.remove = Remove

    self.fileregistry = filereg
    self.teams: dict = None
    self.team_ids = []
    
    self.teams_path = None

  @classmethod
  def bootstrap(cls, filereg, Add=False, Toggle=False, Remove=False):
    logger.info("Bootstrapping the Team module for argument handling")
    obj = cls(filereg=filereg, Add=Add, Toggle=Toggle, Remove=Remove)
    obj.init(misconfigured=False)
    return obj
  
  def init(self, misconfigured=True):
    logger.debug(f"Initializing class {__class__.__name__}")

    teams_template = self.fileregistry.resolve_file("teamsTemplate")
    teams_path = self.fileregistry.resolve_file("teamsPath")

    self.teams_path = teams_path

    if not os.path.exists(teams_path):
      if not os.path.exists(teams_template):
          raise FileNotFoundError(teams_template)

      self.register_teams_file(teams_path, teams_template)

    self.teams = self.load_teams_list()

    self.validate_teams_list(self.teams, exit_if_misconfigured=misconfigured)

    self.team_ids = [str(t).upper() for t in self.teams.get("teams").keys()]
    logger.info(f"{__class__.__name__} initialized successfully")

  def run(self):
    try:
      self._print_teams(without_group_list=self.toggle)
      team_to_update = self._get_valid_team_id()

      if self.add:    result = self.add_team_member(team_to_update)
      if self.remove: result = self.remove_team_member(team_to_update)
      if self.toggle: result = self.toggle_team_view(team_to_update)

      if not result.get("STATUS"):
        raise Exception(result.get("MESSAGE"))
      
      logger.info(result.get("MESSAGE"))

    except ValueError:
      logger.error("Invalid team ID")
      handle_shutdown(1, reason=e)
    except Exception as e:
      logger.error(f"Error updating team list: {e}")
      handle_shutdown(1)

  def _print_teams(self, without_group_list: bool):
    print('Current team configuration:\n')
    team_list = self.teams.get("teams")

    for team, data in team_list.items():
      if without_group_list and str(team).upper() == "GROUP":
        continue

      member_list = ', '.join(data.get('members', []))
      viewable: bool = data.get('viewable', False)

      viewable_line = (
        f" Viewable: {'Y' if viewable else 'N'}\n"
        if str(team).upper() != "GROUP"
        else ""
      )

      print(
        f"{str(team).upper()}:\n"
        f"{viewable_line}"
        f" List: {member_list if len(member_list) > 0 else 'Empty'}\n"
      )

  def _request_team_id(self):
    if self.add:
      return get_non_empty_input('\nWhich team ID would you like to add a member to? ')
    if self.toggle:
      return get_non_empty_input('\nWhich team ID would you like to toggle visibility? ')
    if self.remove:
      return get_non_empty_input('\nWhich team ID would you like to remove a member from? ')
    handle_shutdown(0)

  def _get_valid_team_id(self):
    while True:
      team_id = self._request_team_id().upper()
      if team_id in self.team_ids:
        return team_id.lower()
      print(f" > {team_id} is not a valid team ID.")
  
  def register_teams_file(self, teams_path, teams_template):
    logger.info("Registering the teams list from the template")
    with open(teams_template, 'r') as template_file:
      template_data = json.load(template_file)

    with open(teams_path, 'w') as teams_file:
      json.dump(template_data, teams_file, indent=2)

    error_reason = "Teams list is empty, the program cannot run without it. \nRun the program with -t to update. Consult with the help page via the -h arguments for assistance."
    handle_shutdown(0, reason=error_reason)

  def load_teams_list(self) -> dict:
    teams_file = self.fileregistry.resolve_file("teamsPath")
    logger.debug("Loading the teams list")
    return load_json_file(teams_file, fatal=True)

  @staticmethod
  def validate_teams_list(teams_list: dict, exit_if_misconfigured=True):
    active_exceptions = []
    try:
      teams: dict = teams_list.get('teams')

      viewable_team_members = []

      for team_name, values in teams.items():
        if team_name != "group":
          if not values.get("members"):
            active_exceptions.append(
              ValueError(
                f"ERROR: Missing the required 'members' key for the {str(team_name).upper()} team in {FileNames.Teams}"
              )
            )
          if type(values.get("viewable")) != bool:
            active_exceptions.append(
              TypeError(
                f"ERROR: The 'viewable' flag in the {str(team_name).upper()} team is missing or the incorrect type!"
              )
            )

          names = values.get("members") if values.get("viewable") else []
          viewable_team_members.extend(names)

      if len(active_exceptions) > 0:
        for exception in active_exceptions:
          logger.error(exception)
        raise exceptions.ConfigurationError(f"The teams list configured in {FileNames.Teams} is invalid")

      name_list = [f"'{str(name).strip()}'" for name in viewable_team_members]

      formated_name_list = ", ".join(name_list)

      if len(formated_name_list) < 1 and exit_if_misconfigured:
        failure_reason = f"No 'Viewable' team list configured. Please utilize the '-t toggle' flag to update or manually update the {FileNames.Teams}"
        raise exceptions.MalformedTeamConfiguration(failure_reason)
      logger.debug(f"Viewable team list has been formated for the downstream SQL")
      return formated_name_list
    except Exception as e:
      raise

  def add_team_member(self, team: str):
    result: bool = False
    message = "Undefined error"
    members_to_add = []

    while True:
      new_member = get_non_empty_input(
        "\nAdd team member (press Q to quit): "
      )
      if new_member.upper() in ["Q", "QUIT"]:
        break

      members_to_add.append(new_member)

    team_data: dict = self.load_teams_list()

    current_team_members: list = (
        team_data.get("teams", {})
                 .get(team, {})
                 .get("members", [])
    )

    for name in members_to_add:
      current_team_members.append(name)
      logger.debug(f"Appended {name} to the in-memory {team} list")
    
    with open(self.teams_path, "w") as f:
      json.dump(team_data, f, indent=2)
    
    message = f"New members successfully added to the {FileNames.Teams} file"
    result = True

    return {"STATUS": result, "MESSAGE": message}

  def remove_team_member(self, team: str):
    result: bool = False
    message = "Undefined error"

    members_to_remove = []

    team_data: dict = self.load_teams_list()

    current_team_members: list = (
        team_data.get("teams", {})
                 .get(team, {})
                 .get("members", [])
    )

    while True:
      old_member = get_non_empty_input(
        "\nRemove team member (press Q to quit): "
      )

      if old_member.upper() in ["Q", "QUIT"]:
        break
      if old_member in current_team_members:
        members_to_remove.append(old_member)
      else:
        print(f"{old_member} is not current configured in the {team} list.")
  
    for name in members_to_remove:
      current_team_members.remove(name)
      logger.debug(f"Removed {name} from the in-memory {team} list")

    with open(self.teams_path, "w") as f:
      json.dump(team_data, f, indent=2)

    message = f"Old members successfully removed from the {FileNames.Teams} file"
    result = True

    return {"STATUS": result, "MESSAGE": message}

  def toggle_team_view(self, team: str):
    result: bool = False
    message = "Undefined error"

    team_data: dict = self.load_teams_list()

    team_visibility_flag = (
        team_data.get("teams", {})
                 .get(team, {})
                 .get("viewable", None)
    )

    team_can_be_toggled= type(team_visibility_flag) == bool

    if not team_can_be_toggled:
      message = f"You are not allowed to toggle the {str(team).upper()} team!"
    else:
      team_data["teams"][team]["viewable"] = not team_visibility_flag

      with open(self.teams_path, "w") as f:
        json.dump(team_data, f, indent=2)

      message = f"The {team} team has been toggled successfully in the {FileNames.Teams} file"
      result = True

    return {"STATUS": result, "MESSAGE": message}