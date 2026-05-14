import os, time
from config.products import Products
from config.cases import Cases
from config.config import Config
from config.filereg import FileReg
from display.engineer import EngineerDisplay
from display.common import CommonDisplay
from logger import logger
from exceptions import ConfigurationError
from utils.variables import FileNames
from utils.helper import concat_group_list, concat_support_engineer_list
from api.api_handler import APIHandler, uploadToTseBoard
from datetime import datetime
from tools.alert import alert
from dataclasses import dataclass
from typing import List

class EngineerHandler:
	def __init__(self, config_data, config_cls: Config, filereg_cls: FileReg, team_cls, debug, send_alerts, isTest, teamsList, display, common_display: CommonDisplay):
		self.config_cls = config_cls
		self.filereg_cls = filereg_cls
		self.config_data = config_data
		self.debug = debug
		self.isTest = isTest
		self.display = display
		self.teams_list = teamsList
		alerts = config_data.get("alerts", {})
		self.send_alerts = send_alerts or alerts.get("send", False)
		self.sound_alerts = alerts.get("sound", None)
		self.poll_interval = config_data.get("rules").get("poll_interval", 30)
		self.queries = config_data.get("queries", {})
		self.color = config_data.get("colors", None)
		self.update_threshold = config_data.get("rules").get("update_threshold", 45)
		self.engineer_name = self.config_data.get("engineer_name")
		self.products = Products()
		self.cases = Cases()
		self.display_util = common_display
		self.vacation_scheduled = None
		self.vacation_return_date = None

	def run(self, isTest):
		logger.debug(f"{__class__.__name__}.run() invoked")

		engineer_name = self.engineer_name
		group_list = concat_group_list(self.teams_list)
		support_engineer_list = concat_support_engineer_list(self.teams_list)
		excluded_products = self.products.load_excluded_products()
		excluded_cases = self.cases.load_excluded_cases(log_event=False)

		query = self.build_query(
			excluded_products = excluded_products,
			group_list = group_list,
			engineer_name = engineer_name,
			support_engineer_list = support_engineer_list
		)

		self.main_loop(
			query=query,
			excluded_products=excluded_products,
			excluded_cases=excluded_cases,
			group_list=group_list,
			support_engineer_list=support_engineer_list
		)

	def main_loop(self, query: str, excluded_products: set, excluded_cases: set, group_list, support_engineer_list):
		logger.debug("Entering the structured loop")

		rerender_due_to_update = False

		while True:
			case_results = self.invoke_api(query, rerender = rerender_due_to_update)

			sorted_case_results = self.sort_cases(
				cases=case_results,
				engineer_name=self.engineer_name,
				excluded_products=excluded_products,
				excluded_cases=excluded_cases,
				group_list=group_list,
				support_engineer_list=support_engineer_list
			)

			self.display_results(case_results=sorted_case_results)

			total_seconds = self.poll_interval * 60
			elapsed = 0

			update_detected = False

			while elapsed < total_seconds:
				time.sleep(10)
				elapsed += 10

				current_excluded_products = self.products.load_excluded_products()

				if (len(current_excluded_products) != len(excluded_products)):
					logger.info(f"The number of products in {FileNames.ExProducts} was changed, the display will be re-rendered")
					excluded_products = current_excluded_products
					rerender_due_to_update = True
					update_detected = True
					break

			if not update_detected:
				rerender_due_to_update = False

	def invoke_api(self, query: str, rerender: bool = False) -> dict:
		logger.debug("Invoking the engineer handler's API call")
		return APIHandler(
				api_url=self.config_data.get("api_url"),
				username=self.config_data.get("username"),
				query=query,
				test=self.isTest,
				config_cls=self.config_cls,
				filereg_cls=self.filereg_cls,
				rerender=rerender
			).run()
	
	def display_results(self, case_results: dict):
		self.display_util.clear_screen()
		self.display_util.display_header(self.poll_interval)

		if self.forwarding_agent(): 
			logger.debug("Display canceled, the system is acting as a forwarding agent")
			uploadToTseBoard(case_results, self.config_cls)
		else:
			dashboard = DashboardData(
				team_cases = case_results.get("team_cases"),
				personal_cases = case_results.get("personal_cases"),
				opened_today_cases = case_results.get("opened_today_cases"),
				update_threshold = self.update_threshold,
				color = self.color,
				vacation_scheduled = self.vacation_scheduled,
				vacation_return_date = self.vacation_return_date
			)
			logger.debug("Rendering the display for the engineer flow")
			self.display(dashboard).render()

			case_validation_failed_list = case_results.get("case_validation_failed_list")

			if len(case_validation_failed_list) > 0:
				logger.info(f"Cases failed validation: {case_validation_failed_list}")
				self.display_util.failed_validation(case_validation_failed_list, self.color)
			
			self.send_alert(case_results.get("team_cases"))
	
	def sort_cases(self, cases: dict, engineer_name: str, excluded_products: dict, excluded_cases: dict, group_list: dict, support_engineer_list: dict):
		logger.debug("Sorting the cases into their resepective list based on the response from the API")

		team_cases = []
		personal_cases = []
		opened_today_cases = []
		case_validation_failed_list = []

		for idx, case in enumerate(cases):
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

		logger.debug("Sort of cases has completed, returning the listings")

		return {
			"team_cases": team_cases,
			"personal_cases": personal_cases,
			"opened_today_cases": opened_today_cases,
			"case_validation_failed_list": case_validation_failed_list
		}	

	def send_alert(self, queue_cases: dict):
		if os.name != "nt" and self.send_alerts:
			alert(queue_cases, self.isTest, self.sound_alerts)

	def forwarding_agent(self) -> bool:
		return self.config_cls.get_config_value("rules.upload_to_tse_board", default=False)

	def build_query(self, excluded_products, group_list, engineer_name, support_engineer_list):
		logger.debug(f"Building the query for the engineer role")
		excluded_product_list = "', '".join(excluded_products)
		excluded_product_list = f"'{excluded_product_list}'"

		upload_to_tse_board_enabled = self.forwarding_agent()

		if upload_to_tse_board_enabled:
			logger.debug("Query built for the engineer forwarding agent")
			return self.queries["Engineer_Forwarding"].format(
				excluded_product_list=excluded_product_list,
				support_group=group_list,
				engineer_name=engineer_name,
				support_engineer_list=support_engineer_list
			)
		else:
			logger.debug("Query built for the engineer flow")
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