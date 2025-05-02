import os
import time
from api import http_handler
from display import (
	clear_screen, display_header, display_team, display_personal,
	display_opened_today, display_team_needs_commitment,
	display_queue_needs_commitment
)
from helper import (
  concat_team_list, concat_group_list, concat_support_engineer_list
)
from config import DEBUG
from notification import notify
from exceptions import ConfigurationError, UnsupportedRole

class EngineerHandler:
	def __init__(self, config, debug, send_notification):
		self.salesforce_config, self.supported_products_dict, self.poll_interval, self.queries, *_ , self.teams_list, self.sound_notifications = config
		self.debug = debug
		self.send_notification = send_notification

	def run(self):
		func = "EngineerHandler.run()"
		def log(msg): DEBUG(self.debug, f"{func}: {msg}")

		api_url = self.salesforce_config.get("url")
		username = self.salesforce_config.get("username")
		engineer_name = self.salesforce_config.get("engineer_name")

		if not api_url:
			raise ConfigurationError(f"{func}; Missing Salesforce API in the configuration file.")
		if not username:
			raise ConfigurationError(f"{func}; Missing username in the configuration file.")
		if not engineer_name:
			raise ConfigurationError(f"{func}; Missing engineer name in the configuration file.")

		supported_products = [p for p, is_supported in self.supported_products_dict.items() if is_supported]
		if not supported_products:
			raise ConfigurationError("At least one product must be true in supported_products.")

		product_list = "', '".join(supported_products)
		product_list = f"'{product_list}'"

		group_list = concat_group_list(self.teams_list)
		support_engineer_list = concat_support_engineer_list(self.teams_list)

		query = self.queries["Engineer"].format(
			product_name=product_list,
			support_group=group_list,
			engineer_name=engineer_name,
			support_engineer_list=support_engineer_list
		)

		while True:
			if not self.debug:
				clear_screen()
				display_header(self.poll_interval, self.debug)

			team_cases = []
			personal_cases = []
			opened_today_cases = []

			log("Fetching Engineer query")
			all_cases = http_handler(api_url, username, self.config_password, query, self.debug)

			for case in all_cases:
				owner_name = case.get("Owner", {}).get("Name", "")
				product = case.get("Product__r", {}).get("Name", "")

				if product in supported_products and owner_name in group_list:
					team_cases.append(case)

				if engineer_name.lower() in owner_name.lower():
					personal_cases.append(case)

				if owner_name in support_engineer_list and engineer_name.lower() not in owner_name.lower():
					opened_today_cases.append(case)

			display_team(team_cases, self.debug)
			display_personal(personal_cases, self.debug)
			display_opened_today(opened_today_cases, self.debug)

			if os.name != "nt" and self.send_notification:
				notify(team_cases, self.debug, self.sound_notifications)

			log(f"Sleeping for {self.poll_interval} minutes...")
			time.sleep(self.poll_interval * 60)

	def set_password(self, password):
		self.config_password = password

class ManagerHandler:
	def __init__(self, config, debug, send_notification):
		self.salesforce_config, self.supported_products_dict, self.poll_interval, self.queries, *_ , self.teams_list, self.sound_notifications = config
		self.debug = debug
		self.send_notification = send_notification

	def run(self):
		func = "ManagerHandler.run()"
		def log(msg): DEBUG(self.debug, f"{func}: {msg}")

		api_url = self.salesforce_config.get("url")
		username = self.salesforce_config.get("username")

		if not api_url:
			raise ConfigurationError(f"{func}; Missing Salesforce API in the configuration file.")
		if not username:
			raise ConfigurationError(f"{func}; Missing username in the configuration file.")

		team_names = concat_team_list(self.teams_list)
		group_list = concat_group_list(self.teams_list)

		manager_query = self.queries["Manager"].format(
			support_group=group_list,
			team_list=team_names
		)

		while True:
			if not self.debug:
				clear_screen()
				display_header(self.poll_interval, self.debug)

			log("Fetching team data for manager query")
			cases = http_handler(api_url, username, self.config_password, manager_query, self.debug)

			queue_needs_commitment = []
			team_needs_commitment = []

			for case in cases:
				owner_name = case.get("Owner", {}).get("Name", "")
				commitment_time = case.get("Time_Before_Next_Update_Commitment__c")
				# Should make this value configurable, 0.03125 is 45 minutes.
				# This value is also in the Query itself to it would need to change there as well
				# May want to have a threshold value in the config.json so the user can configure themselves
				if owner_name in group_list and commitment_time is not None and commitment_time <= 0.03125:
					queue_needs_commitment.append(case)

				elif owner_name in team_names and commitment_time is not None and 0 < commitment_time <= 1:
					team_needs_commitment.append(case)

			display_team_needs_commitment(team_needs_commitment, self.debug)
			display_queue_needs_commitment(queue_needs_commitment, self.debug)

			log(f"Sleeping for {self.poll_interval} minutes...")
			time.sleep(self.poll_interval * 60)

	def set_password(self, password):
		self.config_password = password

def role_handler(role, debug, send_notification, config, password):
	func = "role_handler()"
	role = role.upper()
	if role == "ENGINEER":
		handler = EngineerHandler(config, debug, send_notification)
	elif role == "MANAGER":
		handler = ManagerHandler(config, debug, send_notification)
	else:
		raise UnsupportedRole(f'{func}; Unsupported role "{role.lower()}"')

	handler.set_password(password)
	handler.run()