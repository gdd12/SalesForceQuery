import signal
import sys
from config import (
  load_configuration,
  DEBUG,
  request_password,
  user_role
)
from display import (
  info_logger,
  handle_shutdown
)
from exceptions import APIError, ConfigurationError, UnsupportedRole
from handler import role_handler

def main():
  args = info_logger()
  func = 'main()'

  try:
    print("Starting script")
    config = load_configuration()
    role = user_role()

    def log(msg): DEBUG(debug, f"{func}: {msg}")

    config_debug = config[4]
    send_notifications = config[5]

    debug = args.debug if args.debug else config_debug
    send_notification = args.notify if args.notify else send_notifications


    password = request_password(debug)

    log("The following has all been loaded into memory:")
    for item in [
      "Supported products", "Polling interval", "Engineer's name", "All queries",
      "Debug value", "Username", "Password", "API URL", "Sending notification", "User role"
    ]:
      log(f"  - {item}")

    role_handler(role, debug, send_notification, config, password)

  except ConfigurationError as e:
    print(f"Configuration Error: {e}")
  except APIError as e:
    print(f"API Error: {e}")
  except UnsupportedRole as e:
    print(f"Role Error: {e}")
  except Exception as e:
    print(f"Unexpected Error: {e}")
    sys.exit(1)

signal.signal(signal.SIGINT, handle_shutdown)

if __name__ == "__main__":
	main()