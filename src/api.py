import requests
from requests.auth import HTTPBasicAuth
from config import DEBUG

class APIError(Exception):
  """Raised when there is an issue with an API request."""
  pass

def http_handler(api_url, username, password, query, debug):
  func = "http_handler()"
  DEBUG(debug, f'{func}: Started')
  DEBUG(debug, f'{func}: Setting up basic authentication string via Base64 encoding of Username:Password')
  auth = HTTPBasicAuth(username, password)
  DEBUG(debug, f'{func}: Making HTTP request with query string {query}')
  response = requests.get(api_url, headers={"Content-Type": "application/json"}, auth=auth, params={"q": query})

  if response.status_code == 200:
    DEBUG(debug, f'{func}: HTTP {response.status_code}')
    return response.json().get('records', [])
  if response.status_code in [401, 400]:
    DEBUG(debug, f'{func}: HTTP {response.status_code}. Exiting due to credentials errors.')
    print(f"HTTP Error: {response.status_code} credential issue. Update username/password in config.json")
    DEBUG(debug, f'{func}: Finished')
    raise APIError(f"Error {response.status_code}. Fix your credentials")
  elif response.status_code >= 500:
    DEBUG(debug, f'{func}: HTTP {response.status_code}. Server error.')
    raise APIError(f"Error {response.status_code}. Server error.")
  else:
    print(f"Error fetching data from Salesforce: {response.status_code} - {response.text}")
    DEBUG(debug, f'{func}: Finished')
    raise APIError(f"Error {response.status_code}. Unable to fetch data.")
