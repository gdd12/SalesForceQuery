import requests, os
from requests.auth import HTTPBasicAuth
from exceptions import APIError
from logger import logger
from config.config import Config, load_json_file, create_json_file
import json
from utils.variables import FileNames
from tools.encryption import decrypt_password

def http_handler(api_url, username, query, isTest, config_cls, filereg_cls):
  last_query_result = filereg_cls.resolve_file("dataBuffer")

  def hit_api():
    logger.debug("API call invoked!")
    logger.debug(f"Using query: {query}")
    logger.debug(f"HTTP request to {api_url}")

    auth = HTTPBasicAuth(username, decrypt_password())
    response = requests.get(api_url, headers={"Content-Type": "application/json"}, auth=auth, params={"q": query}, timeout=30)

    logger.debug(f"Response took {response.elapsed} and resulted in HTTP {response.status_code}")
    return response

  def fetch_from_api():
    response = hit_api()
    if response.status_code != 200:
      _handle_http_error(response, query, config_cls)

    max_size = config_cls.get_config_value("rules.max_buffer_size_bytes")

    content = response.content
    response_data = response.json()

    if len(content) > max_size:
      logger.error(f"Response size {len(content)} exceeds {max_size}. {FileNames.QueryResults} will not be written to.")
      return response_data
    
    create_json_file(path=last_query_result, data=response_data)
    return response_data

  if isTest and os.path.exists(last_query_result):
    try:
      logger.info(f"Test mode enabled. Loaded mock data from {last_query_result}")
      response_data = load_json_file(last_query_result, fatal=True)
    except json.JSONDecodeError as e:
      logger.error(f"Failed to decode JSON from {last_query_result}: {e}")
      raise APIError("Invalid test response file format.")
  else:
    if isTest:
      logger.info("Test mode enabled but no cached data found. Hitting the API.")
    response_data = fetch_from_api()

  return response_data.get('records', [])

def _handle_http_error(response, query, config_class):
  error_messages = {
    400: f"Query is possibly wrong or malformed.\nUsing query '{query}'",
    401: "Bad credentials",
  }

  try:
    response_json = response.json()
    config_class.remove_key_files()
  except Exception:
    response_json = {}

  if response.status_code in error_messages:
    logger.debug(f"Received response: {response_json}")
    raise APIError(f"HTTP {response.status_code} {response.reason}")

  if response.status_code >= 500:
    logger.debug(f"Received response: {response}")
    logger.error(f"{response.status_code} {response.reason}. Server error.")
    raise APIError(f"HTTP {response.status_code} server error.")

  logger.error(f"Unexpected error: {response.status_code} {response.reason} - {response.text}")
  raise APIError(f"Error {response.status_code} {response.reason}. Unable to fetch data.")

def uploadToTseBoard(cases, config_class):
  tseBoardApi = config_class.get_config_value('front_end_board', default="http://localhost:3000/api/v1/uploadCases")
  payload = {
    "nextPollSetting": config_class.get_config_value("rules.poll_interval"),
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