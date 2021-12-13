import unittest
import csv
import sqlite3
import os
import subprocess
from backports.tempfile import TemporaryDirectory
from parameterized import parameterized
import pandas as pd
import itertools

from tests.unit.RFBaseTest import RFBaseTestCase
from complex_model.GulcalcToBin import gulcalc_sqlite_to_bin, SUPPORTED_GUL_STREAMS, gulcalc_create_header
from complex_model.Common import ArgumentOutOfRangeException


TEST_DIR = os.path.dirname(__file__)
TEST_INPUT_DIR = os.path.join(TEST_DIR, 'data', 'input', 'u_lossoasis_r254')
TEST_MODEL_DATA_DIR = os.path.join(TEST_DIR, 'data', 'model_data')
GULTOCSV = "/oasis/ktools/gultocsv"


def load_csv(con, csv_file, reg_col='item_id'):
    """Loads a gul csv output from oasis gulcalc (or complex model gulcalc) into the sqlite table u_lossoasis_r254"""
    cur = con.cursor()
    cur.execute("CREATE TABLE oasis_loss (event_id INTEGER, loc_id INTEGER, sample_id INTEGER, loss REAL);")

    with open(csv_file, 'r') as fin:
        dr = csv.DictReader(fin)
        to_db = [(int(i['event_id']), int(i[reg_col]), int(i['sidx']), float(i['loss'])) for i in dr]

    cur.executemany("INSERT INTO oasis_loss (event_id, loc_id, sample_id, loss) VALUES (?, ?, ?, ?);", to_db)
    con.commit()


def recreate_csv_from_bin(working_dir, file_fp, stream_name="loss"):
    """This recreates an in memory sqlite database from an oasis gul csv output"""
    gul_fp = os.path.join(working_dir, "gul.bin")

    con = sqlite3.connect(":memory:")
    if stream_name in SUPPORTED_GUL_STREAMS:
        reg_id = "coverage_id" if stream_name == "coverage" else "item_id"
        load_csv(con, file_fp, reg_id)
        stream_id = SUPPORTED_GUL_STREAMS[stream_name]
    else:
        raise ArgumentOutOfRangeException("Unsupported stream: " + stream_name)
    with open(gul_fp, 'wb') as gul_file:
        gulcalc_create_header(gul_file, 1, stream_id)
        gulcalc_sqlite_to_bin(con, gul_file, False)
    con.close()

    gul_csv_fp = os.path.join(working_dir, "gul.csv")
    subprocess.check_call(f"{GULTOCSV} < {gul_fp} > {gul_csv_fp}", stderr=subprocess.STDOUT, shell=True)
    return gul_csv_fp


class GulcalcToBinTests(RFBaseTestCase):
    """Test that the implementation of the GulcalcToBin functionality generates a binary stream
    compatible with the current specification of oasis streams.
    """

    @parameterized.expand([[i, s] for i, s in itertools.product(range(0, 4), list(SUPPORTED_GUL_STREAMS.keys()))])
    def test_event_ordering(self, file_id, stream_type):
        test_filename = f"test_{file_id}_{stream_type}.csv"
        with TemporaryDirectory() as working_dir:
            file_fp = os.path.join(TEST_INPUT_DIR, test_filename)
            gul_csv_fp = recreate_csv_from_bin(working_dir, file_fp, stream_type)

            expected = pd.read_csv(gul_csv_fp)
            self.assertTrue(pd.Index(expected["event_id"]).is_monotonic)

    @parameterized.expand([[i, s] for i, s in itertools.product(range(0, 4), list(SUPPORTED_GUL_STREAMS.keys()))])
    def test_sidx_ordering(self, file_id, stream_type):
        test_filename = f"test_{file_id}_{stream_type}.csv"
        with TemporaryDirectory() as working_dir:
            file_fp = os.path.join(TEST_INPUT_DIR, test_filename)
            gul_csv_fp = recreate_csv_from_bin(working_dir, file_fp, stream_type)

            expected = pd.read_csv(gul_csv_fp)
            last_sid = -4
            last_loc_batch = 0
            for _, row in expected.iterrows():
                current_loc_batch = row["coverage_id"] if "coverage_id" in row else row["item_id"]
                if last_loc_batch == 0:
                    last_loc_batch = current_loc_batch
                sidx = row["sidx"]
                if last_loc_batch != current_loc_batch:
                    last_sid = -4
                self.assertLess(last_sid, sidx)
                last_sid = sidx

    @parameterized.expand([[i, s] for i, s in itertools.product(range(0, 4), list(SUPPORTED_GUL_STREAMS.keys()))])
    def test_multi_packets_stream(self, file_id, stream_type):
        test_filename = f"test_{file_id}_{stream_type}.csv"
        with TemporaryDirectory() as working_dir:
            file_fp = os.path.join(TEST_INPUT_DIR, test_filename)
            gul_csv_fp = recreate_csv_from_bin(working_dir, file_fp, stream_type)

            with open(gul_csv_fp, "r") as gul_csv_file:
                result = set(gul_csv_file.read().splitlines())

            with open(file_fp, "r") as expected_csv:
                expected = set(expected_csv.read().splitlines())

            self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
