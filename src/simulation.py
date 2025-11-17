import warnings
warnings.filterwarnings("ignore")
import signal
import re
from config import load_configuration, request_password
from api import http_handler
from helper import define_query_columns
from main import signal_handler

def simulate(logger):
  print("\n******************** Entering Simulation Env ********************")
  print("*****************************************************************\n")
  logger.info('Entering simulation environment!')
  config = load_configuration()
  salesforce_config = {
    "url": config.get("api_url", ""),
    "username": config.get("username", ""),
    "engineer_name": config.get("engineer_name", "")
  }
  debug = config.get("debug", False)

  api_url = salesforce_config.get("url")
  username = salesforce_config.get("username")

  query = query_builder()
  columns = define_query_columns(query)
  
  if columns: print(f"Selected columns include: {columns}")
  if not debug: print(f'Using query: {query}')

  password = request_password()
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

def query_builder():
  query = input('Enter query: ')
  placeholders = re.findall(r"\{(.*?)\}", query)

  values = {}
  for placeholder in placeholders:
    user_input = input(f"Enter value for '{placeholder}': ")
    values[placeholder] = user_input

  formatted_query = query.format(**values)

  return formatted_query

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
  print('Simulation Environment!')
  simulate()