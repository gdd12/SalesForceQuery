from logger import logger
from handlers.engineer import EngineerHandler
from handlers.manager import ManagerHandler
import exceptions

from display.engineer import EngineerDisplay
from display.manager import ManagerDisplay
from display.common import CommonDisplay

ROLE_CONFIG = {
	"ENGINEER": {
		"handler": EngineerHandler,
		"display": EngineerDisplay,
	},
	"MANAGER": {
		"handler": ManagerHandler,
		"display": ManagerDisplay,
	}
}

def role_handler(role, debug, send_notification, config, isTest, teamsList):
	func = "role_handler()"
	role = role.upper()
	role_config = ROLE_CONFIG.get(role)
	
	if not role_config:
		logger.error(f"Unsupported role '{role.lower()}'")
		raise exceptions.UnsupportedRole(f'{func} failure due to unsupported role "{role.lower()}"')

	handler_class = role_config["handler"]
	display = role_config["display"]()
	
	handler = handler_class(
		common_display=CommonDisplay(),
		display=display,
		config=config,
		debug=debug,
		send_notification=send_notification,
		isTest=isTest,
		teamsList=teamsList
	)
	handler.run(isTest)