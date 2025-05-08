import signal
from config import load_configuration, DEBUG, request_password
from api import http_handler
from helper import define_query_columns
from display import handle_shutdown

def simulate():
  func = "simulate()"
  salesforce_config, supported_products, poll_interval, queries, debug, send_notifications, teams_list, sound_notifications = load_configuration()

  def log(msg): DEBUG(debug, f"{func}: {msg}")

  api_url = salesforce_config.get("url")
  username = salesforce_config.get("username")

  log("Requesting password")
  password = request_password(debug)
  log("Requesting query")
  query = input('Enter query: ')

  columns = define_query_columns(query)
  
  if columns: print(f"Selected columns include: {columns}")
  if not debug: print(f'Using query: {query}')
  log("Calling HTTP handler with the following values")
  log(f'{func}: {api_url} :: {username} :: {debug}')

  response = http_handler(api_url,username,password,query,debug)
  for idx, record in enumerate(response, start=1):
    print(f"----- Record {idx} -----")
    for column in columns:
      if '.' in column:
        parts = column.split('.')
        item = record.get(parts[0], {}).get(parts[1], 'None')
      else:
        item = record.get(column, 'None')
      print(f"{column}: {item}")

signal.signal(signal.SIGINT, handle_shutdown)

if __name__ == "__main__":
  simulate()