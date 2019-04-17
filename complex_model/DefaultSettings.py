""""This contains default values for the gulcalc setting"""
import configparser
config = configparser.ConfigParser()
config.read("/var/oasis/complex_model/engine.ini")

COUNTRY_CODE = "au"
DEFAULT_PORTFOLIO_ID = 1
MAX_DEGREE_OF_PARALLELISM = config['default']['MAX_DEGREE_OF_PARALLELISM'] \
    if 'default' in config and'MAX_DEGREE_OF_PARALLELISM' in config['default'] else 20
DEFAULT_INDIVIDUAL_RISK_MODE = True
DEFAULT_STATIC_MOTOR = False
DEFAULT_RF_PERIL_ID = 2


# oasis file paths
WORKER_LOG_DIRECTORY = "/var/log/oasis"
COMPLEX_MODEL_DIRECTORY = "/var/oasis/complex_model"
MODEL_DATA_DIRECTORY = "/var/oasis/model_data"
TEMP_DIRECTORY_ROOT = config['default']['TEMP_DIRECTORY'] \
    if 'default' in config and 'TEMP_DIRECTORY' in config['default'] else None


