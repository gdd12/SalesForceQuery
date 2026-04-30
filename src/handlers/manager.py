import time
from display.manager import ManagerDisplay
from display.common import CommonDisplay
from logger import logger
from exceptions import ConfigurationError
from utils.helper import concat_group_list, concat_team_list
from api import http_handler

class ManagerHandler:
	def __init__(self, config, debug, send_notification, isTest, teamsList):
		notifications = config.get("notifications", {})
		self.send_notification = send_notification or notifications.get("send", False)
		self.sound_notifications = notifications.get("sound", None)
		self.salesforce_config = {
			"url": config.get("api_url", ""),
			"username": config.get("username", ""),
			"engineer_name": config.get("engineer_name", "")
		}
		self.poll_interval = config.get("rules").get("poll_interval", 30)
		self.queries = config.get("queries", {})
		self.debug = debug or config.get("debug", False)
		self.isTest = isTest
		self.teams_list = teamsList
		self.role = config.get("role", "").upper()
		self.color = config.get("colors", None)
		self.update_threshold = config.get("rules").get("update_threshold", 45)
		self.display = ManagerDisplay()
		self.display_util = CommonDisplay()

	def run(self, isTest):
		logger.debug(f"Class {__class__.__name__} has been invoked")

		api_url = self.salesforce_config.get("url")
		username = self.salesforce_config.get("username")

		if not api_url:
			raise ConfigurationError(f"Missing Salesforce API in the configuration file.")
		if not username:
			raise ConfigurationError(f"Missing username in the configuration file.")

		team_names = concat_team_list(self.teams_list)
		group_list = concat_group_list(self.teams_list)

		manager_query = self.queries["Manager"].format(
			support_group=group_list,
			team_list=team_names,
			update_threshold=(self.update_threshold / (24 * 60))
		)
		logger.debug(f"The Manager query has been formated with configured Teams and update thresholds")

		logger.debug(f"Inside manager handler loop")
		while True:
			self.display_util.clear_screen()
			self.display_util.display_header(self.poll_interval)

			cases = http_handler(api_url, username, manager_query, isTest)

			queue_needs_commitment = []
			team_needs_commitment = []

			for case in cases:
				owner_name = case.get("Owner", {}).get("Name", "")
				commitment_time = case.get("Time_Before_Next_Update_Commitment__c")

				if owner_name in group_list and commitment_time is not None and commitment_time <= (self.update_threshold / (24 * 60)):
					queue_needs_commitment.append(case)

				elif owner_name in team_names and commitment_time is not None and commitment_time <= 1:
					team_needs_commitment.append(case)

			self.display.team_commitment(team_needs_commitment, self.update_threshold, self.color)
			self.display.queue_commitment(queue_needs_commitment, self.update_threshold, self.color)

			logger.debug(f"Sleeping for {self.poll_interval} minutes.")
			time.sleep(self.poll_interval * 60)