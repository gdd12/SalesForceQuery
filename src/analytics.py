import os
import json
import datetime
from exceptions import EventError, EventPurgeError
from logger import logger
from config import readFileReg, resolve_registry_path, file_exists, get_config_value

memorized_cases = set()

def loadEventsFilePath():
	file_reg = readFileReg()
	events_reg = resolve_registry_path(file_reg, "events")
	return events_reg

def createOrCheckEventsFile():
	max_byte_size = get_config_value("max_event_file_size_in_Bytes")
	try:
		path = loadEventsFilePath()
		if not file_exists(path):
			with open(path, 'w'):
				pass
		else:
			file_size = os.path.getsize(path)
			if file_size > max_byte_size:
				logger.error(f'{path} size of {file_size} exceeds configured byte size: {max_byte_size}')
				purgeEvents()

		return path
	except Exception as e:
		raise EventError(f"Failed to create or check event file: {e}")

def createEvent(event_dict, idx):
	try:
		case_number = event_dict.get("CaseNumber")
		if case_number in memorized_cases:
			return

		event_populated = {
			"CaseNumber": case_number,
			"CreatedDate": '',
			"Owner": event_dict.get("Owner", {}).get("Name"),
			"Product": event_dict.get("Product__r", {}).get("Name"),
			"Status": event_dict.get("Status"),
			"NextUpdate": event_dict.get("Time_Before_Next_Update_Commitment__c"),
			"isClosed": event_dict.get("Status_Closed__c"),
			"Priority": event_dict.get("Severity__c")
		}

		json_line = json.dumps(event_populated) + "\n"

		path = loadEventsFilePath()
		max_byte_size = get_config_value("max_event_file_size_in_Bytes")

		if os.path.exists(path):
			current_size = os.path.getsize(path)
			if current_size + len(json_line.encode("utf-8")) > max_byte_size:
				logger.warning(
					f"File size would exceed limit with next write ({current_size} + {len(json_line.encode('utf-8'))} > {max_byte_size}). Purging..."
				)
				purgeEvents()

		with open(path, "a") as f:
			f.write(json_line)
			logger.debug(f"Wrote event: {case_number}")

		memorized_cases.add(case_number)

	except Exception as e:
		raise EventError(f"Failed to create event: {e}")

def processEvents(data):
	try:
		createOrCheckEventsFile()
		loadExistingCaseNumbers()
		idx = 0
		for event in data:
			idx += 1
			createEvent(event, idx)

	except EventError as e:
		raise EventError(e)

def purgeEvents():
	file = loadEventsFilePath()
	try:
		logger.info("Purging the events file")
		os.remove(file)
	except EventPurgeError as e:
		raise EventPurgeError(e)
	logger.info('Purged events.jsonl')
	createOrCheckEventsFile()
	return

def loadExistingCaseNumbers():
	try:
		path = loadEventsFilePath()
		if not file_exists(path):
			return

		with open(path, 'r') as f:
			logger.info('Added to the memorized set')
			for line in f:
				try:
					event = json.loads(line.strip())
					case_number = event.get("CaseNumber")
					if case_number:
							memorized_cases.add(case_number)
				except json.JSONDecodeError:
					continue
	except Exception as e:
		raise EventError(f"Failed to load existing events: {e}")