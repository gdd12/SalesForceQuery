import requests
from requests.auth import HTTPBasicAuth
from config import DEBUG
from exceptions import APIError

def http_handler(api_url, username, password, query, debug):
  func = "http_handler()"
  def log(msg): DEBUG(debug, f"{func}: {msg}")

  log("Started")
  auth = HTTPBasicAuth(username, password)
  log("Making HTTP request with query string:")
  log(query)

  response = requests.get(api_url, headers={"Content-Type": "application/json"}, auth=auth, params={"q": query})

  log(f"HTTP {response.status_code}")

  if response.status_code == 200:
    return response.json().get('records', [])

  error_messages = {
    400: f"Bad request. Query is possibly wrong or malformed. Using query '{query}'",
    401: f"Bad credentials",
  }

  if response.status_code in error_messages:
    log(error_messages[response.status_code])
    log("Finished")
    raise APIError(f"HTTP {response.status_code} {response.reason}. {error_messages[response.status_code]}")

  if response.status_code >= 500:
    log(f"{response.status_code} {response.reason}. Server error.")
    raise APIError(f"HTTP {response.status_code} server error.")

  print(f"Error fetching data from Salesforce: {response.status_code} {response.reason} - {response.text}")
  log("Finished")
  raise APIError(f"Error {response.status_code} {response.reason}. Unable to fetch data.")
