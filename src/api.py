import requests
from requests.auth import HTTPBasicAuth
from config import DEBUG
from exceptions import APIError

import logging
logger = logging.getLogger()

def http_handler(api_url, username, password, query, debug):

  auth = HTTPBasicAuth(username, password)
  logger.info(f"HTTPBasicAuth completed")

  logger.info(f"Making HTTP request")
  response = requests.get(api_url, headers={"Content-Type": "application/json"}, auth=auth, params={"q": query})

  if response.status_code == 200:
    logger.info(f"HTTP {response.status_code} Continuing with response processing")
    return response.json().get('records', [])

  error_messages = {
    400: f"Bad request. Query is possibly wrong or malformed. Using query '{query}'",
    401: f"Bad credentials",
  }

  if response.status_code in error_messages:
    logger.error(error_messages[response.status_code])
    raise APIError(f"HTTP {response.status_code} {response.reason}. {error_messages[response.status_code]}")

  if response.status_code >= 500:
    logger.error(f"{response.status_code} {response.reason}. Server error.")
    raise APIError(f"HTTP {response.status_code} server error.")

  print(f"Error fetching data from Salesforce: {response.status_code} {response.reason} - {response.text}")
  raise APIError(f"Error {response.status_code} {response.reason}. Unable to fetch data.")
