import time
from display.manager import ManagerDisplay
from display.common import CommonDisplay
from logger import logger
from exceptions import ConfigurationError
from utils.helper import concat_group_list, concat_team_list
from api import http_handler
from dataclasses import dataclass
from typing import List

class ManagerHandler:
	def __init__(self, config_data, config_cls, filereg_cls, team_cls, debug, send_notification, isTest, teamsList, display, common_display):
		self.config_cls = config_cls
		self.filereg_cls = filereg_cls
		self.config_data = config_data
		self.poll_interval = config_data.get("rules").get("poll_interval", 30)
		self.queries = config_data.get("queries", {})
		self.teams_list = teamsList
		self.color = config_data.get("colors", None)
		self.update_threshold = config_data.get("rules").get("update_threshold", 45)
		self.display = display
		self.display_util = common_display

	def run(self, isTest):
		logger.debug(f"Class {__class__.__name__} has been invoked")

		api_url = self.config_data.get("api_url")
		username = self.config_data.get("username")

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

		logger.info(f"Inside manager handler loop")
		while True:
			self.display_util.clear_screen()
			self.display_util.display_header(self.poll_interval)

			cases = http_handler(api_url, username, manager_query, isTest, self.config_cls, self.filereg_cls)

			queue_needs_commitment = []
			team_needs_commitment = []

			for case in cases:
				owner_name = case.get("Owner", {}).get("Name", "")
				commitment_time = case.get("Time_Before_Next_Update_Commitment__c")

				if owner_name in group_list and commitment_time is not None and commitment_time <= (self.update_threshold / (24 * 60)):
					queue_needs_commitment.append(case)

				elif owner_name in team_names and commitment_time is not None and commitment_time <= 1:
					team_needs_commitment.append(case)
			
			dashboard = DashboardData(
				queue_needs_commitment = queue_needs_commitment,
				team_needs_commitment = team_needs_commitment,
				update_threshold = self.update_threshold,
				color = self.color
			)

			self.display(dashboard).render()

			logger.debug(f"Sleeping for {self.poll_interval} minutes.")
			time.sleep(self.poll_interval * 60)

@dataclass
class DashboardData:
	team_needs_commitment: List[dict]
	queue_needs_commitment: List[dict]
	update_threshold: int
	color: List[dict]