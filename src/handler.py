import os
import time
from api import http_handler, uploadToTseBoard
from display import (
	clear_screen, display_header, display_team, display_personal,
	display_opened_today, display_team_needs_commitment,
	display_queue_needs_commitment
)
from helper import (
  concat_team_list, concat_group_list, concat_support_engineer_list
)
from notification import notify
from exceptions import ConfigurationError, UnsupportedRole
from datetime import datetime
from config import load_excluded_cases, get_config_value, request_password, load_excluded_products
from logger import logger
from analytics import processEvents
from variables import FileNames

class EngineerHandler:
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
		self.config_password = None
		
	def run(self, isTest):
		func = "EngineerHandler.run()"
		logger.debug(f"{func} has been invoked")

		api_url = self.salesforce_config.get("url")
		username = self.salesforce_config.get("username")
		engineer_name = self.salesforce_config.get("engineer_name")

		if not api_url:
			logger.error(f"API url is missing from the {FileNames.Config}")
			raise ConfigurationError(f"{func}; Missing Salesforce API in the configuration file.")
		if not username:
			raise ConfigurationError(f"{func}; Missing username in the configuration file.")
		if not engineer_name:
			raise ConfigurationError(f"{func}; Missing engineer name in the configuration file.")


		excluded_products = load_excluded_products()

		excluded_product_list = "', '".join(excluded_products)
		excluded_product_list = f"'{excluded_product_list}'"

		group_list = concat_group_list(self.teams_list)
		support_engineer_list = concat_support_engineer_list(self.teams_list)

	

		logger.debug(f"The Engineer query has been formated with configured Teams, Engineers, Products, and main TSE")

		events_processing_enabled = get_config_value("events.process_events")

		logger.info(f"Inside engineer handler loop")
		while True:
			clear_screen()
			display_header(self.poll_interval)

			excluded_products = load_excluded_products()

			query = self.build_query(
				excluded_products,
				group_list,
				engineer_name,
				support_engineer_list
			)

			team_cases = []
			personal_cases = []
			opened_today_cases = []

			all_cases = http_handler(api_url, username, self.config_password, query, isTest)

			excluded_cases = load_excluded_cases()

			if get_config_value("rules.upload_to_tse_board"): uploadToTseBoard(all_cases)
			else:
				for case in all_cases:
					owner_name = case.get("Owner", {}).get("Name", "")
					product = case.get("Product__r", {}).get("Name", "")
					created_date_str = case.get("CreatedDate", "")
					case_number = case.get("CaseNumber", "").strip()
					
					today = datetime.today()
					if created_date_str: created_date = datetime.strptime(created_date_str[:10], "%Y-%m-%d")
					else: raise Exception(f"Invalid CreatedDate: {'Cannot be null' if len(created_date_str) < 1 else f'{created_date_str}'}")

					if (product not in excluded_products and owner_name in group_list) and (case_number not in excluded_cases):
						team_cases.append(case)

					if engineer_name.lower() in owner_name.lower():
						personal_cases.append(case)

					if owner_name in support_engineer_list and created_date.month == today.month and created_date.day == today.day:
						opened_today_cases.append(case)
				
				display_team(team_cases, self.update_threshold, self.color)
				display_personal(personal_cases, self.update_threshold, self.color)
				display_opened_today(opened_today_cases, self.debug, self.color)

				if os.name != "nt" and self.send_notification:
					notify(team_cases, isTest, self.sound_notifications)

				if events_processing_enabled: processEvents(all_cases)

			num_excluded_products = len(load_excluded_products())
			total_seconds = self.poll_interval * 60
			elapsed = 0

			while elapsed < total_seconds:
				logger.debug(f"WatchDog on {FileNames.ExProducts} executed")
				time.sleep(10)
				elapsed += 10

				if len(load_excluded_products()) != num_excluded_products:
					logger.info(f"WatchDog found {FileNames.ExProducts} was updated - rebuilding query.")
					break

	def set_password(self, password):
		self.config_password = password

	def build_query(self, excluded_products, group_list, engineer_name, support_engineer_list):
		excluded_product_list = "', '".join(excluded_products)
		excluded_product_list = f"'{excluded_product_list}'"

		upload_to_tse_board_enabled = get_config_value("rules.upload_to_tse_board")

		if upload_to_tse_board_enabled:
			return self.queries["Engineer_Forwarding"].format(
				excluded_product_list=excluded_product_list,
				support_group=group_list,
				engineer_name=engineer_name,
				support_engineer_list=support_engineer_list
			)
		else:
			return self.queries["Engineer"].format(
				excluded_product_list=excluded_product_list,
				support_group=group_list,
				engineer_name=engineer_name,
				support_engineer_list=support_engineer_list
			)

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
		self.config_password = None

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

		events_processing_enabled = get_config_value("events.process_events")
		logger.debug(f"Inside manager handler loop")
		while True:
			clear_screen()
			display_header(self.poll_interval)

			cases = http_handler(api_url, username, self.config_password, manager_query, isTest)

			queue_needs_commitment = []
			team_needs_commitment = []

			for case in cases:
				owner_name = case.get("Owner", {}).get("Name", "")
				commitment_time = case.get("Time_Before_Next_Update_Commitment__c")

				if owner_name in group_list and commitment_time is not None and commitment_time <= (self.update_threshold / (24 * 60)):
					queue_needs_commitment.append(case)

				elif owner_name in team_names and commitment_time is not None and commitment_time <= 1:
					team_needs_commitment.append(case)

			display_team_needs_commitment(team_needs_commitment, self.update_threshold, self.color)
			display_queue_needs_commitment(queue_needs_commitment, self.update_threshold, self.color)

			if events_processing_enabled: processEvents(cases)
			logger.debug(f"Sleeping for {self.poll_interval} minutes.")
			time.sleep(self.poll_interval * 60)

	def set_password(self, password):
		self.config_password = password

def role_handler(role, debug, send_notification, config, isTest, teamsList):
	func = "role_handler()"
	role = role.upper()
	if role == "ENGINEER":
		handler = EngineerHandler(config, debug, send_notification, isTest, teamsList)
	elif role == "MANAGER":
		handler = ManagerHandler(config, debug, send_notification, isTest, teamsList)
	else:
		logger.error(f"Unsupported role '{role.lower()}'")
		raise UnsupportedRole(f'{func}; Unsupported role "{role.lower()}"')

	handler.set_password(request_password())
	handler.run(isTest)