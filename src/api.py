import requests
from requests.auth import HTTPBasicAuth
from config import DEBUG
from exceptions import APIError

def http_handler(api_url, username, password, query, debug):
  func = "http_handler()"
  DEBUG(debug, f'{func}: Started')
  auth = HTTPBasicAuth(username, password)
  DEBUG(debug, f'{func}: Making HTTP request with query string:')
  DEBUG(debug, f'{func}: {query}')
  response = requests.get(api_url, headers={"Content-Type": "application/json"}, auth=auth, params={"q": query})

  if response.status_code == 200:
    DEBUG(debug, f'{func}: HTTP {response.status_code}')
    return response.json().get('records', [])
  if response.status_code in [401, 400]:
    DEBUG(debug, f'{func}: HTTP {response.status_code}. Exiting due to credentials errors.')
    DEBUG(debug, f'{func}: Finished')
    raise APIError(f"HTTP {response.status_code} {response.reason}. Username is incorrect in config.json or entered invalid password")
  elif response.status_code >= 500:
    DEBUG(debug, f'{func}: HTTP {response.status_code} {response.reason}. Server error.')
    raise APIError(f"HTTP {response.status_code} server error.")
  else:
    print(f"Error fetching data from Salesforce: {response.status_code} {response.reason} - {response.text}")
    DEBUG(debug, f'{func}: Finished')
    raise APIError(f"Error {response.status_code} {response.reason}. Unable to fetch data.")
