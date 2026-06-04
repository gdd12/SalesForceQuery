from exceptions import BadQuery, ConfigurationError, MalformedTeamConfiguration
import sys
from logger import logger
import re
from datetime import datetime, date

def define_query_columns(query):
	upper_query = query.upper()
	try:
		if "SELECT" not in upper_query or "FROM" not in upper_query:
			raise BadQuery("Missing SELECT or FROM clause in query.")
        
		start = upper_query.index("SELECT") + len("SELECT")
		end = upper_query.index("FROM")
		columns_str = query[start:end].strip()

		columns = [col.strip() for col in columns_str.split(',')]
		return columns

	except BadQuery as e:
		print(f"BadQuery error: {e}")
		return []

def convert_days_to_dhm(day_value):
	if day_value is None:
		return "0M"
	
	total_minutes = int(round(day_value * 24 * 60))
	days = total_minutes // (24 * 60)
	hours = (total_minutes % (24 * 60)) // 60
	minutes = total_minutes % 60
	if day_value < 0:
		return 'Missed'
	parts = []
	if days:
		parts.append(f"{days}D")
	if hours:
		parts.append(f"{hours}H")
	if minutes or not parts:
		parts.append(f"{minutes}M")

	return " ".join(parts)

def concat_group_list(teams_list: dict) -> str:
	group_list_raw = teams_list.get("teams", {}).get("group", {}).get("members", "")
	quoted_group = [f"'{group.strip()}'" for group in group_list_raw]
	logger.debug(f"Group list has been formated for the downstream SQL")
	return ", ".join(quoted_group)

def concat_team_list(teams_list):
	from config.team import Team
	return Team.validate_teams_list(teams_list, exit_if_misconfigured=True)

def handle_shutdown(exit_code=0, reason='', module="Main"):
	logger.info(f"{module} module shutdown code: {exit_code} {reason}")
	if reason:
		print(reason)
	if exit_code == 0:
		sys.exit(0)
	if exit_code == 1:
		sys.exit(1)

def calculate_days_delta(date):
	logger.debug(f"Vacation return date was set to {date}, calculating the delta")
	months = [
		"January", "February", "March", "April", "May", "June",
		"July", "August", "September", "October", "November", "December"
	]
	pattern = r'^([A-Za-z]+)\s+(-?\d+)$'
	match = re.match(pattern, date.strip())
	
	if not match:
		return None
	
	month_str, day_str = match.groups()
	
	if month_str.capitalize() not in months:
		return None
	
	day = int(day_str)
	month = months.index(month_str.capitalize()) + 1
	
	try:
		today = datetime.today().date()
		input_date = datetime(today.year, month, day).date()
	except ValueError:
		return None
	
	delta = input_date - today
	return delta.days

def get_non_empty_input(prompt):
	try:
		while True:
			value = input(prompt).strip()
			if value:
				return value
			print("This field cannot be empty.")
	except KeyboardInterrupt:
		handle_shutdown(0)

def print_help_page():
  print("""
Usage: main.py [any of the below arguments]

Configuration:
  -c                  Display the current config.json settings

  -r                  Change active role

  -t <add|remove|toggle>
											Manage the teams list
                        Ex: -t add
                        Ex: -t remove
												Ex: -t toggle

  -e <case|product> <VALUE>
                      Add an exclusion to the ignore list. 
                        Ex: -e case 0156872
                        Ex: -e case RESET
                        Ex: -e product

  -v <MONTH> <DAY>    Set a scheduled vacation return date to
                      validate pending commitments

Runtime Options:
  -q                    Simulate SQL queries against Salesforce
  -s                    Run interactive configuration setup
  -test                 Run in test mode. Skips API calls if ~/config/dataBuffer.json does not exist
  -clean                Remove system-generated config files without deleting user data.

Debug Options:
  -d                    Enable debug logging
""")
  return