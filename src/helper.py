from exceptions import BadQuery, ConfigurationError

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
	name_list = []

	for data in names_list.values():
		if data.get("viewable"):
			raw_list = data.get("list", "")
			name_list += [name.strip() for name in raw_list.split(',') if name.strip()]

	if not name_list:
		raise ConfigurationError("Must have at least one 'viewable' team with names in the configuration file.")

	name_string = ", ".join(f"'{name}'" for name in name_list)
	return name_string