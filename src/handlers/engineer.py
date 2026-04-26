import os, time
from config.products import Products
from config.cases import Cases
from config.config import Config
from display.engineer import EngineerDisplay
from display.common import CommonDisplay
from logger import logger
from exceptions import ConfigurationError
from utils.variables import FileNames
from utils.helper import concat_group_list, concat_support_engineer_list
from api import http_handler, uploadToTseBoard
from datetime import datetime
from tools.notify import notify

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
		self.products = Products()
		self.cases = Cases()
		self.config = Config()
		self.display = EngineerDisplay()
		self.display_util = CommonDisplay()

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

		group_list = concat_group_list(self.teams_list)
		support_engineer_list = concat_support_engineer_list(self.teams_list)

		logger.debug(f"The Engineer query has been formated with configured Teams, Engineers, Products, and main TSE")

		logger.info(f"Inside engineer handler loop")
		while True:
			self.display_util.clear_screen()
			self.display_util.display_header(self.poll_interval)

			excluded_products = self.products.load_excluded_products()

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

			excluded_cases = self.cases.load_excluded_cases()

			if self.config.get_config_value("rules.upload_to_tse_board"): uploadToTseBoard(all_cases)
			else:
				case_validation_failed_list = []
				for idx, case in enumerate(all_cases):
					owner_name = case.get("Owner", {}).get("Name", "")
					product = case.get("Product__r", {}).get("Name", "")
					created_date_str = case.get("CreatedDate", "")
					case_number = (case.get("CaseNumber", "") or "").strip()
					
					today = datetime.today()
					if created_date_str: created_date = datetime.strptime(created_date_str[:10], "%Y-%m-%d")

					if not owner_name or not product or not created_date_str or not case_number:
						logger.warning(f"Invalid Case Properties at idx {idx} of the {FileNames.QueryResults}. Skipping this case.")
						case_validation_failed_list.append({"CaseNumber": case_number, "Index": idx})
						continue
		
					if (product not in excluded_products and owner_name in group_list) and (case_number not in excluded_cases):
						team_cases.append(case)

					if engineer_name.lower() in owner_name.lower():
						personal_cases.append(case)

					if owner_name in support_engineer_list and created_date.month == today.month and created_date.day == today.day:
						opened_today_cases.append(case)

				self.display.queue(team_cases, self.update_threshold, self.color)
				self.display.personal(personal_cases, self.update_threshold, self.color)
				self.display.opened_today(opened_today_cases, self.debug, self.color)

				if len(case_validation_failed_list) > 0:
					logger.info(f"Cases failed validation: {case_validation_failed_list}")
					self.display_util.failed_validation(case_validation_failed_list, self.color)

				if os.name != "nt" and self.send_notification:
					notify(team_cases, isTest, self.sound_notifications)

			num_excluded_products = len(self.products.load_excluded_products())
			total_seconds = self.poll_interval * 60
			elapsed = 0

			while elapsed < total_seconds:
				logger.debug(f"WatchDog on {FileNames.ExProducts} executed")
				time.sleep(10)
				elapsed += 10

				if len(self.products.load_excluded_products()) != num_excluded_products:
					logger.info(f"WatchDog found {FileNames.ExProducts} was updated - rebuilding query.")
					break

	def set_password(self, password):
		self.config_password = password

	def build_query(self, excluded_products, group_list, engineer_name, support_engineer_list):
		excluded_product_list = "', '".join(excluded_products)
		excluded_product_list = f"'{excluded_product_list}'"

		upload_to_tse_board_enabled = self.config.get_config_value("rules.upload_to_tse_board")

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