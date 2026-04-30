from logger import logger
from handlers.engineer import EngineerHandler
from handlers.manager import ManagerHandler
from exceptions import UnsupportedRole

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

	handler.run(isTest)