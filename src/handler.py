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

		team_query = self.queries["EQ_team_queue"].format(product_name=product_list, support_group=group_list)
		personal_query = self.queries["EQ_personal_queue"].format(product_name=product_list, engineer_name=engineer_name)
		opened_today_query = self.queries["EQ_opened_today"].format(product_name=product_list, support_engineer_list=support_engineer_list)

		while True:
			if not self.debug:
				clear_screen()
				display_header(self.poll_interval, self.debug)

			log("Fetching team cases")
			team_cases = http_handler(api_url, username, self.config_password, team_query, self.debug)

			log("Fetching personal cases")
			personal_cases = http_handler(api_url, username, self.config_password, personal_query, self.debug)

			log("Fetching opened today cases")
			opened_today_cases = http_handler(api_url, username, self.config_password, opened_today_query, self.debug)

			display_team(team_cases, self.debug)
			if personal_cases:
				display_personal(personal_cases, self.debug)
			if opened_today_cases:
				display_opened_today(opened_today_cases, self.debug)

			if os.name != "nt" and self.send_notification:
				notify(team_cases, self.debug, self.sound_notifications)

			log(f"Sleeping for {self.poll_interval} minutes...")
			time.sleep(self.poll_interval * 60)

	def set_password(self, password):
		self.config_password = password

class ManagerHandler:
	def __init__(self, config, debug, send_notification):
		self.salesforce_config, self.supported_products_dict, self.poll_interval, self.queries, *_ , self.teams_list = config
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

		team_needs_commitment_query = self.queries["MQ_team_needs_commitment"]
		queue_needs_commitment_query = self.queries["MQ_queue_needs_commitment"]

		team_names = concat_team_list(self.teams_list)
		group_list = concat_group_list(self.teams_list)

		queue_needs_commitment_query = queue_needs_commitment_query.format(support_group=group_list)
		team_needs_commitment_query = team_needs_commitment_query.format(team_list=team_names)

		while True:
			if not self.debug:
				clear_screen()
				display_header(self.poll_interval, self.debug)

			log("Fetching team needs commitment")
			team_needs_commitment = http_handler(api_url, username, self.config_password, team_needs_commitment_query, self.debug)

			log("Fetching queue needs commitment")
			queue_needs_commitment = http_handler(api_url, username, self.config_password, queue_needs_commitment_query, self.debug)

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