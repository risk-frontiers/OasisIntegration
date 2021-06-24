""""This contains default values for the gulcalc setting"""
import os


COUNTRY_CODE = "au"
DEFAULT_PORTFOLIO_ID = 1
MAX_DEGREE_OF_PARALLELISM = 10
DEFAULT_BATCH_EXPOSURE_SIZE = 100
DEFAULT_INDIVIDUAL_RISK_MODE = True
DEFAULT_STATIC_MOTOR = False
DEFAULT_DEMAND_SURGE = False
DEFAULT_INPUT_SCALING = 0.0
DEFAULT_RF_PERIL_ID = 2
DEFAULT_SEED = 1
BASE_DB_NAME = 'riskfrontiersdbAUS_v2_6.db'
DEFAULT_HAILAUS_DB = 'riskfrontiersdbHAILAUS_v2_6'


# oasis file paths
WORKER_LOG_DIRECTORY = "/var/log/oasis"
WORKER_LOG_FILE = os.path.join(WORKER_LOG_DIRECTORY, "worker.log")
COMPLEX_MODEL_DIRECTORY = "/home/worker/complex_model"
MODEL_DATA_DIRECTORY = "/var/oasis/model_data"

# misc
RF_DEBUG_MODE = False
