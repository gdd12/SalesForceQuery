import os, json
from pathlib import Path
from utils.variables import FileNames, VARS
from datetime import datetime
from config.config import load_json_file, create_json_file
from utils.helper import logger

class Counter():
	def __init__(self):
		self.path = Path(__file__).resolve().parent.parent.parent / VARS.Config / FileNames.Counter
	
	def validate(self, force_rebuild=False):
		try:
			if not self.path.exists() or force_rebuild:
				default_data = {
					"dateSet": f"{(datetime.now().date())}",
					"counter": 0
				}
				create_json_file(path=self.path, data=default_data)

			counter = load_json_file(self.path)
			return counter
		except Exception as e:
			raise e

	def increment(self):
		ctr_data = self.validate()

		ctr_count = ctr_data.get("counter")
		ctr_date = ctr_data.get("dateSet")

		today = datetime.now().date()

		try:
			ctr_date = datetime.fromisoformat(ctr_date).date()
		except Exception:
			logger.exception("Invalid date in counter file, resetting.")
			self.reset()
			ctr_data = self.validate()
			ctr_count = 0
			ctr_date = today

		if ctr_date < today:
			logger.info("Counter has expired, resetting for today.")
			self.reset()
			return False
		
		if ctr_count >= 20:
			logger.info("Counter limit reached, resetting for today")
			self.reset()
			return False

		ctr_count += 1
		ctr_data["counter"] = ctr_count

		with open(self.path, "w") as f:
			json.dump(ctr_data, f, indent=2)

		return True
	
	def reset(self):
		self.validate(force_rebuild=True)
		return
	
	def ok(self):
		return self.increment()