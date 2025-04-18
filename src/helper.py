from exceptions import BadQuery

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
