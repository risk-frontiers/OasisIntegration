import argparse
import os
import json
import sys
import logging
import subprocess

import pandas as pd

from backports.tempfile import TemporaryDirectory
from oasislmf.utils.exceptions import OasisException
from OasisToRF import create_rf_input, DEFAULT_DB, get_connection_string
from GulcalcToBin import gulcalc_sqlite_to_bin
from Common import PerilSet

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

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

_DEBUG = True


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
    model_settings = analysis_settings_json['analysis_settings']['model_settings']

    # Read the inputs, including the extended items
    with open(os.path.join(inputs_fp, 'coverages.csv')) as p:
        coverages_pd = pd.read_csv(p)

    # with open(os.path.join(inputs_fp, 'gulsummaryxref.csv')) as p:
    #    gulsummaryxref_pd = pd.read_csv(p)

    with open(complex_items_fp) as p:
        items_pd = pd.read_csv(p)

    with TemporaryDirectory() as working_dir:
        if _DEBUG:
            working_dir = "/hadoop/oasis/tmp"
        # Write out RF canonical input files
        risk_platform_dir = os.path.join("/var/oasis/model_data", "RISKFRONTIERS/HAILAUS")  # todo: make this generic
        if not os.path.isfile(os.path.join(risk_platform_dir, DEFAULT_DB)):
            raise FileNotFoundError("Model data not set correctly")
        temp_db_fp = os.path.join(working_dir, DEFAULT_DB)

        # populate RF exposure and coverage datatable
        num_rows = create_rf_input(items_pd, coverages_pd, temp_db_fp, risk_platform_dir)

        # Call Risk.Platform.Core
        max_event_id = PerilSet[model_version_id]['MAX_EVENT_INDEX']
        # 1 generate oasis_param.json
        oasis_param = {
            "Peril": 2,
            "ItemConduit": {"DbBrand": 1, "ConnectionString": get_connection_string(temp_db_fp)},
            "CoverageConduit": {"DbBrand": 1, "ConnectionString": get_connection_string(temp_db_fp)},
            "ResultConduit": {"DbBrand": 1, "ConnectionString": get_connection_string(temp_db_fp)},
            "MinEventId": int((event_batch - 1) * max_event_id / max_event_batch) + 1,
            "MaxEventId": int(event_batch * max_event_id / max_event_batch),
            "NumSamples": int(number_of_samples),
            "CountryCode": "au",  # todo: get this from somewhere
            "ComplexModelDirectory": "/var/oasis/complex_model",
            "RiskPlatformData": risk_platform_dir,
            "WorkingDirectory": working_dir,
            "NumRows": num_rows,
            "PortfolioId": 1,
            "IndividualRiskMode": model_settings['irm'] if 'irm' in model_settings else False,
            "StaticMotor": model_settings['static_motor'] if 'static_motor' in model_settings else False,
        }

        oasis_param_fp = os.path.join(working_dir, "oasis_param.json")
        with open(oasis_param_fp, 'w') as param:
            param.writelines(json.dumps(oasis_param, indent=4, separators=(',', ': ')))

        # 2 call dotnet Risk.Platform.Core/Risk.Platform.Core.dll --oasis -c oasis_param.json
        # todo: replace with self contained call
        cmd_str = "{} --oasis -c {} {}".format(os.path.join(oasis_param["ComplexModelDirectory"],
                                                            "Risk.Platform.Core",
                                                            "Risk.Platform.Core"),
                                               oasis_param_fp, "--debug" if _DEBUG else "")
        try:
            subprocess.check_call(cmd_str, stderr=subprocess.STDOUT, shell=True)
            if do_coverage_output:
                gulcalc_sqlite_to_bin(temp_db_fp, output_item, int(number_of_samples), 2)
            elif do_item_output:
                gulcalc_sqlite_to_bin(temp_db_fp, output_coverage, int(number_of_samples), 1)

        except subprocess.CalledProcessError as e:
            raise OasisException(e)


if __name__ == "__main__":
    main()

