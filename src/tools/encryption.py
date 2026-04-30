import os
from cryptography.fernet import Fernet
from getpass import getpass
from utils.variables import FileNames, VARS
from logger import logger
from utils.helper import handle_shutdown
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / VARS.Config
passwd_file = os.path.join(CONFIG_PATH, FileNames.PasswordFile)
key_file = os.path.join(CONFIG_PATH, FileNames.KeyFile)

def generate_key():
	if not os.path.exists(key_file):
		key = Fernet.generate_key()
		with open(key_file, "wb") as f:
			f.write(key)

def load_key():
	with open(key_file, "rb") as f:
		return f.read()

def generate_encrypted_passwd():
	try:
		generate_key()
		key = load_key()
		fernet = Fernet(key)

		password = getpass("API Password: ").encode()
		encrypted_password = fernet.encrypt(password)

		with open(passwd_file, "wb") as f:
			f.write(encrypted_password)
		logger.info("API password encrypted")
	except KeyboardInterrupt:
		handle_shutdown(exit_code=0, reason="User canceled the entry")

def decrypt_password():
	try:
		key = load_key()
		fernet = Fernet(key)

		with open(passwd_file, "rb") as f:
			encrypted_password = f.read()

		decrypted_password = fernet.decrypt(encrypted_password)
		return decrypted_password.decode()
	except Exception:
		return