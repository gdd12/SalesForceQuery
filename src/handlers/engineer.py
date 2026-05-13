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
from dataclasses import dataclass
from typing import List

class EngineerHandler:
	def __init__(self, config_data, config_cls, filereg_cls, team_cls, debug, send_notification, isTest, teamsList, display, common_display):
		self.config_cls = config_cls
		self.filereg_cls = filereg_cls
		self.config_data = config_data
		self.debug = debug
		self.isTest = isTest
		self.display = display
		self.teams_list = teamsList
		notifications = config_data.get("notifications", {})
		self.send_notification = send_notification or notifications.get("send", False)
		self.sound_notifications = notifications.get("sound", None)
		self.poll_interval = config_data.get("rules").get("poll_interval", 30)
		self.queries = config_data.get("queries", {})
		self.color = config_data.get("colors", None)
		self.update_threshold = config_data.get("rules").get("update_threshold", 45)
		self.products = Products()
		self.cases = Cases()
		self.display_util = common_display
		self.vacation_scheduled = None
		self.vacation_return_date = None

	def run(self, isTest):
		func = "EngineerHandler.run()"
		logger.debug(f"{func} has been invoked")

		api_url = self.config_data.get("api_url")
		username = self.config_data.get("username")
		engineer_name = self.config_data.get("engineer_name")

		group_list = concat_group_list(self.teams_list)
		support_engineer_list = concat_support_engineer_list(self.teams_list)

		self.vacation_scheduled = self.config_cls.get_config_value("rules.vacation_scheduled")
		self.vacation_return_date = self.config_cls.get_config_value("rules.back_from_vacation")

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

			all_cases = http_handler(api_url, username, query, isTest, self.config_cls, self.filereg_cls)

			excluded_cases = self.cases.load_excluded_cases()

			if self.config_cls.get_config_value("rules.upload_to_tse_board"): uploadToTseBoard(all_cases, self.config_cls)
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

				dashboard = DashboardData(
					team_cases = team_cases,
					personal_cases = personal_cases,
					opened_today_cases = opened_today_cases,
					update_threshold = self.update_threshold,
					color = self.color,
					vacation_scheduled = self.vacation_scheduled,
					vacation_return_date = self.vacation_return_date
				)

				self.display(dashboard).render()

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

	def build_query(self, excluded_products, group_list, engineer_name, support_engineer_list):
		excluded_product_list = "', '".join(excluded_products)
		excluded_product_list = f"'{excluded_product_list}'"

		upload_to_tse_board_enabled = self.config_cls.get_config_value("rules.upload_to_tse_board")

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

@dataclass
class DashboardData:
	team_cases: List[dict]
	personal_cases: List[dict]
	opened_today_cases: List[dict]
	update_threshold: int
	vacation_scheduled: bool
	vacation_return_date: str
	color: List[dict]