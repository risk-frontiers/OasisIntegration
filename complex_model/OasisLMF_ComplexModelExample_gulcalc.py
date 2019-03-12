import argparse
import os
import json
import sys
import struct
import logging

import pandas as pd

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

    complex_items_filename = args.complex_items_filename
    complex_items_fp = os.path.join(inputs_fp, complex_items_filename)
    if not os.path.exists(complex_items_fp):
        raise Exception('Complex items file does not exist')

    analysis_settings_json = json.load(open(analysis_settings_fp))
    number_of_samples = analysis_settings_json['analysis_settings']['number_of_samples']
    
    # Access any model specific settings for the analysis
    model_settings = analysis_settings_json['analysis_settings']['model_settings']

    # Read the inputs, including the extended items
    with os.popen('coveragetocsv < {}'.format(
            os.path.join(inputs_fp, 'coverages.bin'))) as p:
        coverages_pd = pd.read_csv(p)

    with os.popen('gulsummaryxreftocsv < {}'.format(
            os.path.join(inputs_fp, 'gulsummaryxref.bin'))) as p:
        gulsummaryxref_pd = pd.read_csv(p)

    with os.popen('complex_itemtocsv < {}'.format(complex_items_fp)) as p:
        items_pd = pd.read_csv(p)

    # Write simulated GULs to stdout
    if do_item_output:
        item_stream_id = (1 << 24) | 1
        output_item.write(struct.pack('i', item_stream_id))
        output_item.write(struct.pack('i', number_of_samples))
    if do_coverage_output:
        coverage_stream_id = (1 << 24) | 2
        output_coverage.write(struct.pack('i', coverage_stream_id))
        output_coverage.write(struct.pack('i', number_of_samples))

    max_event_id = 1000
    for event_id in range(
         int((event_batch - 1) * max_event_id/max_event_batch) + 1,
         int(event_batch * max_event_id/max_event_batch)+ 1):

        # Losses by sample index by item
        item_samples = {}
        # Coverages by sample index by item
        coverage_samples = {}

        for _, row in items_pd.iterrows():
            item_id = row["item_id"]
            coverage_id = row["coverage_id"]
            if item_id not in item_samples:
                item_samples[item_id] = {}
            if coverage_id not in coverage_samples:
                coverage_samples[coverage_id] = {}

            # Special sample IDs:
            # -1 : Numerically integrated mean
            # -2 : Numerically integrated stddev
            for sample_idx in \
                    (-1, -2) + tuple(range(1, number_of_samples + 1)):
                loss_sample = 1000000.0
                item_samples[item_id]

                if sample_idx not in item_samples[item_id]:
                    item_samples[item_id][sample_idx] = loss_sample
                if sample_idx in coverage_samples[coverage_id]:
                    coverage_samples[coverage_id][sample_idx] += loss_sample
                else:
                    coverage_samples[coverage_id][sample_idx] = loss_sample

        if do_item_output:
            for item_id in item_samples:
                output_item.write(struct.pack('i', event_id))
                output_item.write(struct.pack('i', item_id))
                for sample_idx in sorted(item_samples[item_id]):
                    output_item.write(struct.pack('i', sample_idx))
                    output_item.write(struct.pack('f', loss_sample))
                output_item.write(struct.pack('i', 0))
                output_item.write(struct.pack('f', 0.0))
        if do_coverage_output:
            for coverage_id in coverage_samples:
                output_coverage.write(struct.pack('i', event_id))
                output_coverage.write(struct.pack('i', coverage_id))
                for sample_idx in sorted(item_samples[item_id]):
                    output_coverage.write(struct.pack('i', sample_idx))
                    output_coverage.write(struct.pack('f', loss_sample))
                output_coverage.write(struct.pack('i', 0))
                output_coverage.write(struct.pack('f', 0.0))


if __name__ == "__main__":
    main()
