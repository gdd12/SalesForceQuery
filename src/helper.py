from exceptions import BadQuery, ConfigurationError
import sys

from logger import setup_logger
logger = setup_logger()

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

def concat_team_list(names_list):
	func = "concat_team_list()"
	name_list = []

	for data in names_list.values():
		if data.get("viewable"):
			raw_list = data.get("list", "")
			name_list += [name.strip() for name in raw_list.split(',') if name.strip()]

	if not name_list:
		raise ConfigurationError(f"{func} failed: Must have at least one 'viewable' team with names in the configuration file.")

	name_string = ", ".join(f"'{name}'" for name in name_list)
	return name_string

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

def concat_group_list(teams_list):
	group_list_raw = teams_list.get("group", {}).get("list", "")
	group_names = group_list_raw.split(",")
	quoted_group = [f"'{group.strip()}'" for group in group_names]
	logger.info(f"Group list has undergone formating for SQL query")
	return ", ".join(quoted_group)

def concat_support_engineer_list(teams_list):
	other_names = []
	for k, v in teams_list.items():
		if k != "group":
			names = v["list"].split(",")
			other_names.extend(names)

	quoted_names = [f"'{name.strip()}'" for name in other_names]
	logger.info(f"TSE list has undergone formating for SQL query")
	return ", ".join(quoted_names)

def handle_shutdown(exit_code=0):
	if exit_code == 0:
		logger.info(f"Shutdown code: {exit_code}")
		sys.exit(0)
	if exit_code == 1:
		logger.error(f"Shutdown code: {exit_code}")
		sys.exit(1)