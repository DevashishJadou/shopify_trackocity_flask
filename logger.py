# Imports the Google Cloud client library
from google.cloud import logging
import os

root_dir = os.path.abspath(os.path.dirname(__file__))
_credential_path = "stagging-trackocity_logger_key.json"
_CLIENT_SECRET_PATH = os.path.join(root_dir, _credential_path)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = _CLIENT_SECRET_PATH

# Instantiates a client
logging_client = logging.Client()

def auth_logger():
	# The name of the log to write to
	log_name = "projects/stagging-leadly-client/logs/signin"
	# Selects the log to write to
	logger = logging_client.logger(log_name)

	return logger, log_name
