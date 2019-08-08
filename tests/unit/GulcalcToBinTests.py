import unittest
import csv
import sqlite3
import os
import subprocess
from backports.tempfile import TemporaryDirectory
from parameterized import parameterized
import pandas as pd

from tests.unit.RFBaseTest import RFBaseTestCase
from complex_model.GulcalcToBin import gulcalc_sqlite_to_bin


TEST_DIR = os.path.dirname(__file__)
TEST_INPUT_DIR = os.path.join(TEST_DIR, 'data', 'input', 'u_lossoasis_r254')
TEST_MODEL_DATA_DIR = os.path.join(TEST_DIR, 'data', 'model_data')


def load_csv(con, csv_file, reg_col='coverage_id'):
    cur = con.cursor()
    cur.execute("CREATE TABLE u_lossoasis_r254 (event_id INTEGER, reg_id INTEGER, sample_id INTEGER, groundup REAL);")

    with open(csv_file, 'r') as fin:
        dr = csv.DictReader(fin)
        to_db = [(int(i['event_id']), int(i[reg_col]), int(i['sidx']), float(i['loss'])) for i in dr]

    cur.executemany("INSERT INTO u_lossoasis_r254 (event_id, reg_id, sample_id, groundup) VALUES (?, ?, ?, ?);", to_db)
    con.commit()


def recreate_csv_from_bin(working_dir, file_fp):
    gul_fp = os.path.join(working_dir, "gul.bin")

    con = sqlite3.connect(":memory:")
    load_csv(con, file_fp)
    with open(gul_fp, 'wb') as gul_file:
        gulcalc_sqlite_to_bin(con, gul_file, 1, 2)
    con.close()

    gul_csv_fp = os.path.join(working_dir, "gul.csv")
    subprocess.check_call("gultocsv < {} > {}".format(gul_fp, gul_csv_fp), stderr=subprocess.STDOUT, shell=True)
    return gul_csv_fp


class GulcalcToBinTests(RFBaseTestCase):
    """Test that the implementation of the GulcalcToBin functionality generates a binary stream
    compatible with the current specification of oasis streams.
    """

    @parameterized.expand([["test_1.csv".format(i)] for i in range(1, 4)] + [["gul.csv"]])
    def test_event_ordering(self, test_filename):
        with TemporaryDirectory() as working_dir:
            file_fp = os.path.join(TEST_INPUT_DIR, test_filename)
            gul_csv_fp = recreate_csv_from_bin(working_dir, file_fp)

            expected = pd.read_csv(gul_csv_fp)
            self.assertTrue(pd.Index(expected["event_id"]).is_monotonic)

    @parameterized.expand([["test_1.csv".format(i)] for i in range(1, 4)] + [["gul.csv"]])
    def test_sidx_ordering(self, test_filename):
        with TemporaryDirectory() as working_dir:
            file_fp = os.path.join(TEST_INPUT_DIR, test_filename)
            gul_csv_fp = recreate_csv_from_bin(working_dir, file_fp)

            expected = pd.read_csv(gul_csv_fp)
            last_sid = -2
            for _, row in expected.iterrows():
                sidx = row["sidx"]
                if sidx == -1:
                    self.assertNotEqual(-1, last_sid)
                elif sidx < 0:
                    self.assertLessEqual(sidx, last_sid)
                else:
                    self.assertLessEqual(last_sid, sidx)
                last_sid = sidx

    @parameterized.expand([["test_{}.csv".format(i)] for i in range(0, 4)] + [["gul.csv"]])
    def test_multi_packets_stream(self, test_filename):
        with TemporaryDirectory() as working_dir:
            file_fp = os.path.join(TEST_INPUT_DIR, test_filename)
            gul_csv_fp = recreate_csv_from_bin(working_dir, file_fp)

            with open(gul_csv_fp, "r") as gul_csv_file:
                result = set(gul_csv_file.read().splitlines())

            with open(file_fp, "r") as expected_csv:
                expected = set(expected_csv.read().splitlines())

            self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
