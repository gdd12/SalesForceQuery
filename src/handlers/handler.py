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

class Handler():
	def __init__(self, config, filereg, team, counter):
		self.config = config
		self.filereg = filereg
		self.team = team
		self.counter = counter

	def init(self):
		logger.info(f"{__class__.__name__} initialized successfully")

	def run(self, role, debug, send_alerts, config_data, isTest, teamsList):
		if type(role) != str:
			raise TypeError(f"Role must be of type 'string'")
		
		role = str(role).upper()
		role_config = ROLE_CONFIG.get(role)

		if not role_config:
			logger.error(f"Unsupported role '{role.lower()}'")
			raise exceptions.UnsupportedRole(f'{__class__.__name__} failure due to unsupported role "{role.lower()}"')

		handler_class = role_config["handler"]
		display = role_config["display"]

		handler = handler_class(
			common_display=CommonDisplay(),
			config_cls = self.config,
			filereg_cls = self.filereg,
			team_cls = self.team,
			display=display,
			config_data=config_data,
			debug=debug,
			send_alerts=send_alerts,
			isTest=isTest,
			teamsList=teamsList
		)
		handler.run(isTest)