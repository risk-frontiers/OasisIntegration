import argparse
import os
import json
import sys
import logging
import subprocess

import pandas as pd
import complex_model.DefaultSettings as DS

from backports.tempfile import TemporaryDirectory
from oasislmf.utils.exceptions import OasisException
from complex_model.OasisToRF import create_rf_input, DEFAULT_DB, get_connection_string, is_valid_model_data
from complex_model.GulcalcToBin import gulcalc_sqlite_fp_to_bin
from complex_model.Common import PerilSet
from complex_model.RFException import FileNotFoundException
from datetime import datetime
import multiprocessing


PY3K = sys.version_info >= (3, 0)

if PY3K:
    output_stdout = sys.stdout.buffer
else:
    # Python 2 on Windows opens sys.stdin in text mode, and
    # binary data that read from it becomes corrupted on \r\n
    if sys.platform == "win32":
        # set sys.stdin to binary mode
        import msvcrt

        msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)
    output_stdout = sys.stdout

_DEBUG = False
_WORKER_LOG_FILE = "/var/log/oasis/worker.log"
logging.basicConfig(level=logging.DEBUG if _DEBUG else logging.INFO,
                    filename=_WORKER_LOG_FILE,
                    format='[%(asctime)s: %(levelname)s/%(filename)s] %(message)s')


def clean_directory(dir_path):
    import shutil
    if os.path.exists(dir_path) and os.path.isdir(dir_path):
        shutil.rmtree(dir_path)
    os.mkdir(dir_path)


def main():
    parser = argparse.ArgumentParser(description='Ground up loss generation.')
    parser.add_argument(
        '-e', '--event_batch', required=True, nargs=2, type=int,
        help='The n_th batch out of m.',
    )
    parser.add_argument(
        '-a', '--analysis_settings_file', required=True,
        help='The analysis settings file.',
    )
    parser.add_argument(
        '-p', '--inputs_directory', required=True,
        help='The inputs directory.',
    )
    parser.add_argument(
        '-f', '--complex_items_filename', default="complex_items.bin",
        help='The complex items file name.',
    )
    parser.add_argument(
        '-i', '--item_output_stream', required=False, default=None,
        help='Items output stream.',
    )
    parser.add_argument(
        '-c', '--coverage_output_stream', required=False, default=None,
        help='Coverage output stream.',
    )
    parser.add_argument(
        '-M', '--model_data_directory', required=False, default=DS.MODEL_DATA_DIRECTORY,
        help='Model data directory.',
    )
    parser.add_argument(
        '-X', '--complex_model_directory', required=False, default=DS.COMPLEX_MODEL_DIRECTORY,
        help='Complex model directory.',
    )

    args = parser.parse_args()

    do_item_output = False
    output_item = None
    if args.item_output_stream is not None:
        do_item_output = True
        if args.item_output_stream == '-':
            output_item = output_stdout
        else:
            output_item = open(args.item_output_stream, "wb")

    do_coverage_output = False
    output_coverage = None
    if args.coverage_output_stream is not None:
        do_coverage_output = True
        if args.coverage_output_stream == '-':
            output_coverage = output_stdout
        else:
            output_coverage = open(args.coverage_output_stream, "wb")

    analysis_settings_fp = args.analysis_settings_file

    if not os.path.exists(analysis_settings_fp):
        raise Exception('Analysis setting file does not exist')

    (event_batch, max_event_batch) = args.event_batch
    if event_batch > max_event_batch:
        raise Exception('Invalid event batch')

    inputs_fp = args.inputs_directory
    if not os.path.exists(inputs_fp):
        raise Exception('Inputs directory does not exist')

    complex_items_filename = "complex_items.csv"  # args.complex_items_filename
    complex_items_fp = os.path.join(inputs_fp, complex_items_filename)
    if not os.path.exists(complex_items_fp):
        raise Exception('Complex items file does not exist')

    analysis_settings_json = json.load(open(analysis_settings_fp))
    number_of_samples = analysis_settings_json['analysis_settings']['number_of_samples']

    # Access any model specific settings for the analysis
    model_version_id = analysis_settings_json['analysis_settings']['model_version_id'].lower()
    if 'model_settings' in analysis_settings_json['analysis_settings']:
        model_settings = analysis_settings_json['analysis_settings']['model_settings']
    else:
        model_settings = {}

    # Read the inputs, including the extended items
    with open(os.path.join(inputs_fp, 'coverages.csv')) as p:
        coverages_pd = pd.read_csv(p)

    # with open(os.path.join(inputs_fp, 'gulsummaryxref.csv')) as p:
    #    gulsummaryxref_pd = pd.read_csv(p)

    with open(complex_items_fp) as p:
        items_pd = pd.read_csv(p)

    with TemporaryDirectory() as working_dir:
        log_filename = "worker_{}_{}.log".format(event_batch, datetime.now().strftime("%Y%m%d%H%M%S"))
        # log_filename = "worker.log"
        log_fp = os.path.join(DS.WORKER_LOG_DIRECTORY, log_filename)
        if _DEBUG:
            working_dir = "/tmp/oasis_debug_{}".format(event_batch)
            clean_directory(working_dir)
            log_fp = os.path.join(working_dir, log_filename)
        logging.info("Working directory for worker with batch " + str(event_batch) + " is set to be " + working_dir)
        logging.info("The process independent log file for this worker is " + log_filename)

        # Write out RF canonical input files
        risk_platform_data = os.path.join(args.model_data_directory)
        if not is_valid_model_data(risk_platform_data):
            message = "Model data not set correctly: " + risk_platform_data
            logging.error(message)
            raise FileNotFoundException(message, 420)
        temp_db_fp = os.path.join(working_dir, DEFAULT_DB)
        logging.info("RF model data file found in " + risk_platform_data)

        # check RF license exists
        licence_file = os.path.join(risk_platform_data, "license.txt")
        if not os.path.isfile(licence_file):
            licence_file = os.path.join(risk_platform_data, "licence.txt")
            if not os.path.isfile(licence_file):
                message = "License file not found at " + risk_platform_data
                logging.error(message)
                raise FileNotFoundException(message, 410)
        logging.info("License file found at " + licence_file)

        # populate RF exposure and coverage datatable
        logging.info("STARTED: Generating RF input database in " + temp_db_fp)
        num_rows = create_rf_input(items_pd, coverages_pd, temp_db_fp, risk_platform_data)
        logging.info("COMPLETED: RF input database generated in " + temp_db_fp + " [OK]")

        # generate oasis_param.json
        complex_model_directory = args.complex_model_directory
        max_event_id = PerilSet[model_version_id]['MAX_EVENT_INDEX']
        num_cores = multiprocessing.cpu_count()
        max_parallelism = int(max(1, min(num_cores, num_cores/max_event_batch)))
        oasis_param = {
            "Peril": DS.DEFAULT_RF_PERIL_ID,
            "ItemConduit": {"DbBrand": 1, "ConnectionString": get_connection_string(temp_db_fp)},
            "CoverageConduit": {"DbBrand": 1, "ConnectionString": get_connection_string(temp_db_fp)},
            "ResultConduit": {"DbBrand": 1, "ConnectionString": get_connection_string(temp_db_fp)},
            "MinEventId": int((event_batch - 1) * max_event_id / max_event_batch) + 1,
            "MaxEventId": int(event_batch * max_event_id / max_event_batch),
            "NumSamples": int(number_of_samples),
            "CountryCode": DS.COUNTRY_CODE,
            "ComplexModelDirectory": complex_model_directory,
            "LicenseFile": licence_file,
            "RiskPlatformData": risk_platform_data,
            "WorkingDirectory": working_dir,
            "NumRows": num_rows,
            "PortfolioId": DS.DEFAULT_PORTFOLIO_ID,
            "MaxDegreeOfParallelism": max_parallelism,
            "IndividualRiskMode": model_settings['individual_risk_mode']
            if 'individual_risk_mode' in model_settings else DS.DEFAULT_INDIVIDUAL_RISK_MODE,
            "StaticMotor": model_settings['static_motor']
            if 'static_motor' in model_settings else DS.DEFAULT_STATIC_MOTOR,
            "DemandSurge": model_settings['demand_surge']
            if 'demand_surge' in model_settings else DS.DEFAULT_DEMAND_SURGE,
            "InputScaling": model_settings['input_scaling']
            if 'input_scaling' in model_settings else DS.DEFAULT_INPUT_SCALING,
        }

        oasis_param_fp = os.path.join(working_dir, "oasis_param.json")
        with open(oasis_param_fp, 'w') as param:
            param.writelines(json.dumps(oasis_param, indent=4, separators=(',', ': ')))
            logging.debug("The Risk Frontiers .Net engine will be called with the following parameters")
            logging.debug(json.dumps(oasis_param, indent=4, separators=(',', ':')))

        # call Risk.Platform.Core/Risk.Platform.Core.dll --oasis -c oasis_param.json [--debug] --log path_to_log.txt
        cmd_str = "{} --oasis -c {} {} --log {}".format(os.path.join(oasis_param["ComplexModelDirectory"],
                                                                     "Risk.Platform.Core", "Risk.Platform.Core"),
                                                        oasis_param_fp,
                                                        "--debug" if _DEBUG else "",
                                                        log_fp)
        try:
            logging.info("STARTED: Calling Risk Frontiers .Net engine: " + cmd_str + " for event batch "
                         + str(event_batch))
            subprocess.check_call(cmd_str, stderr=subprocess.STDOUT, shell=True)
            logging.info("COMPLETED: Loss database has been generated in " + temp_db_fp + " for event batch "
                         + str(event_batch))
            if do_item_output:
                logging.info("STARTED: Transforming sqlite losses into gulcalc item binary stream for event_batch "
                             + str(event_batch))
                gulcalc_sqlite_fp_to_bin(temp_db_fp, output_item, int(number_of_samples), 1)
            if do_coverage_output:
                logging.info("STARTED: Transforming sqlite losses into gulcalc coverage binary stream for event_batch "
                             + str(event_batch))
                gulcalc_sqlite_fp_to_bin(temp_db_fp, output_coverage, int(number_of_samples), 2)
            logging.info("COMPLETED: Successfully generated losses as gulcalc binary stream for event batch "
                         + str(event_batch))
        except subprocess.CalledProcessError as e:
            logging.error("An error occurred while calling the Risk Frontiers .Net engine. Please look at " + log_fp +
                          " for more information regarding this issue")
            raise OasisException(e)


if __name__ == "__main__":
    main()
