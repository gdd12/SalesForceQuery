import requests, os
from requests.auth import HTTPBasicAuth
from exceptions import APIError
from logger import logger
from config.config import Config, load_json_file, create_json_file
from config.filereg import FileReg
import json
from utils.variables import FileNames
from tools.encryption import decrypt_password

class APIHandler():
  def __init__(self, api_url, username, query, test: bool, config_cls: Config, filereg_cls: FileReg, rerender: bool = False):
    self.api_url = api_url
    self.username = username
    self.query = query
    self.test = test
    self.config_cls = config_cls
    self.filereg_cls = filereg_cls
    self.last_query_result = filereg_cls.resolve_file("dataBuffer")
    self.rerender = rerender or False

  def run(self) -> dict:
    if ((self.test_mode() or self.rerender) and self.cached_file_exists()):
      logger.debug(f"{__class__.__name__}.run() invoked to perform a rerender OR is currently in TEST mode")
      response_data = self.load_previous_data()
    else:
      logger.debug(f"{__class__.__name__}.run() invoked to call the API")
      response_data = self.fetch_from_api()

    return response_data.get('records', [])
  
  def test_mode(self) -> bool:
    return self.test and self.cached_file_exists()

  def cached_file_exists(self) -> bool:
    return os.path.exists(self.last_query_result)

  def load_previous_data(self) -> dict:
    try:
      logger.info(f"Loading data from the previous successful API call")
      return load_json_file(self.last_query_result, fatal=True)
    except json.JSONDecodeError as e:
      logger.error(f"Failed to decode JSON from {self.last_query_result}: {e}")
      raise APIError("Invalid test response file format.")

  def hit_api(self) -> requests.Response:
    logger.debug("API call invoked!")
    logger.debug(f"Using query: {self.query}")
    logger.debug(f"HTTP request to {self.api_url}")

    auth = HTTPBasicAuth(self.username, decrypt_password())
    response = requests.get(self.api_url, headers={"Content-Type": "application/json"}, auth=auth, params={"q": self.query}, timeout=30)

    logger.debug(f"Response took {response.elapsed} and resulted in HTTP {response.status_code}")
    return response

  def fetch_from_api(self) -> dict:
    logger.info("Fetching the data from the SalesForce API")
    response = self.hit_api()

    self.validate_response(response)
    response_data = response.json()

    self.cache_response(response.content, response_data)
    return response_data
  
  def validate_response(self, response: requests.Response) -> None:
    logger.debug("Verifying the HTTP response code")

    if response.status_code != 200:
      self.handle_http_error(response)
  
  def cache_response(self, content: bytes, response_data: dict) -> None:
    logger.debug("Attemping to cache the response from the previous API call")

    max_size = self.config_cls.get_config_value("rules.max_buffer_size_bytes")

    if len(content) > max_size:
      logger.error(f"Response size {len(content)} exceeds {max_size}. {FileNames.QueryResults} will not be written to.")
      return
    
    create_json_file(path=self.last_query_result, data=response_data, log_event=False)

  def handle_http_error(self, response: requests.Response) -> None:
    logger.debug("HTTP call resulted in a non 200 code, thus handling the error")
    error_messages = {
      400: f"Query is possibly wrong or malformed.\nUsing query '{self.query}'",
      401: "Bad credentials",
    }
    try:
      response_json = response.json()
      self.config_cls.remove_key_files()
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