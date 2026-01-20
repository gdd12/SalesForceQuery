import requests
from requests.auth import HTTPBasicAuth
from exceptions import APIError
from logger import logger
from config import load_json_file, file_exists, create_json_file, resolve_registry_path, readFileReg, get_config_value
import json

def http_handler(api_url, username, password, query, isTest: False):
  fileReg = readFileReg()
  mock_data = resolve_registry_path(fileReg, "mockData")

  def hitAPI():
    logger.debug("API call invoked!")
    logger.debug(f"Using query: {query}")
    logger.debug(f"HTTP request to {api_url}")
    auth = HTTPBasicAuth(username, password)
    response = requests.get(api_url, headers={"Content-Type": "application/json"}, auth=auth, params={"q": query}, timeout=30)
    return response

  response_data = None

  if isTest:
    if file_exists(mock_data):
      try:
        response_data = load_json_file(mock_data, fatal=True)
        logger.info(f"Test mode enabled. Loaded mock data from {mock_data}")
      except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON from {mock_data}: {e}")
        raise APIError("Invalid test response file format.")
    else:
      logger.info("Test mode enabled, no mock data file found! Hitting API.")
      response = hitAPI()

      if response.status_code == 200:
        response_data = response.json()
        create_json_file(mock_data, response_data)
      else:
        _handle_http_error(response, query)
  else:
    response = hitAPI()
    logger.debug(f"Response took {response.elapsed}")

    if response.status_code == 200:
      response_data = response.json()
    else:
      _handle_http_error(response, query)

  return response_data.get('records', [])

def _handle_http_error(response, query):
  error_messages = {
    400: f"Bad request. Query is possibly wrong or malformed. Using query '{query}'",
    401: "Bad credentials",
  }

  try:
    response_json = response.json()
  except Exception:
    response_json = {}

  if response.status_code in error_messages:
    logger.debug(f"Received response: {response_json}")
    logger.error(f"HTTP {response.status_code}: {error_messages[response.status_code]}")
    raise APIError(f"HTTP {response.status_code} {response.reason}. {error_messages[response.status_code]}")

  if response.status_code >= 500:
    logger.debug(f"Received response: {response}")
    logger.error(f"{response.status_code} {response.reason}. Server error.")
    raise APIError(f"HTTP {response.status_code} server error.")

  logger.error(f"Unexpected error: {response.status_code} {response.reason} - {response.text}")
  raise APIError(f"Error {response.status_code} {response.reason}. Unable to fetch data.")

def uploadToTseBoard(cases):
  tseBoardApi = get_config_value('front_end_board')
  payload = {
    "nextPollSetting": get_config_value("rules.poll_interval"),
    "cases": cases
  }
  try:
    response = requests.post(
      tseBoardApi,
      json=payload,
      timeout=5
    )
    response.raise_for_status()
    logger.info("Upload to TSE board successful!")
    return response.json()
  except requests.exceptions.RequestException as e:
    print(f"Error uploading to TSE Board: {e}")
    logger.error(f"Upload to TSE board failed: {e}")
    return None