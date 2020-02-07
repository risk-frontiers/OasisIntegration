import unittest
import os
from backports.tempfile import TemporaryDirectory
import pandas as pd
import sqlite3

from tests.unit.RFBaseTest import RFBaseTestCase
from complex_model.OasisToRF import create_rf_input, DEFAULT_DB


TEST_DIR = os.path.dirname(__file__)
TEST_INPUT_DIR = os.path.join(TEST_DIR, 'data', 'input')
TEST_MODEL_DATA_DIR = os.path.join(TEST_DIR, 'data', 'model_data')


class CreateDatabaseTests(RFBaseTestCase):
    """This contains tests for the RF inpu database creation logic
    """
    def __create_rf_input_generic(self, expected, subdir):
        items_file = os.path.join(TEST_INPUT_DIR, subdir, 'complex_items.csv')
        with open(items_file, 'r') as f:
            items_pd = pd.read_csv(f)
        coverages_file = os.path.join(TEST_INPUT_DIR, subdir, 'coverages.csv')
        with open(coverages_file, 'r') as f:
            coverages_pd = pd.read_csv(f)
        with TemporaryDirectory() as tmp_dir:
            sqlite_fp = os.path.join(tmp_dir, DEFAULT_DB)
            create_rf_input(items_pd, coverages_pd, sqlite_fp, TEST_MODEL_DATA_DIR)
            con = sqlite3.connect(os.path.join(tmp_dir, DEFAULT_DB))
            cur = con.cursor()
            cur.execute("SELECT * from u_exposure;")
            rows = cur.fetchall()
            self.assertEqual(1, len(rows))
            for i in range(0, len(expected)):
                self.assertEqual(expected[i], rows[0][i])
            con.close()

    def test_create_rf_input_address(self):
        expected = ('1', -35.201133, 149.038656, 1, 'GAACT714845933', 0, 'au', 'ACT', 2, 39, 4, 161, 3, 39, 1, 2615,
                    None, None, 1, '{"YearBuilt": 0}', None, 1)
        self.__create_rf_input_generic(expected, 'address')

    def test_cresta_rf_input_address_yearbuilt(self):
        expected = ('1', -35.201133, 149.038656, 1, 'GAACT714845933', 0, 'au', 'ACT', 2, 39, 4, 161, 3, 39, 1, 2615,
                    None, None, 1, '{"YearBuilt": 2019}', None, 1)
        self.__create_rf_input_generic(expected, 'address_yearbuilt')

    def test_create_rf_input_latlon(self):
        expected = ('1', -35.201133, 149.038656, None, None, 7, 'au', None, None, None, None, None, None, None,
                    1, 2615, None, None, 1, '{"YearBuilt": 0}', None, 1)
        self.__create_rf_input_generic(expected, 'latlon')

    def test_create_rf_input_postcode(self):
        expected = ('1', None, None, None, None, 1, 'au', None, None, None, None, None, None, None,
                    1, 2615, None, None, 1, '{"YearBuilt": 0}', None, 1)
        self.__create_rf_input_generic(expected, 'postcode')

    def test_create_rf_input_cresta(self):
        expected = ('1', None, None, None, None, 2, 'au', None, 2, 39, None, None, None, None, None, None,
                    None, None, 1, '{"YearBuilt": 0}', None, 1)
        self.__create_rf_input_generic(expected, 'cresta')

    def test_create_rf_input_ica_zone(self):
        expected = ('1', None, None, None, None, 3, 'au', None, None, None, None, None, 3, 39, None, None,
                    None, None, 1, '{"YearBuilt": 0}', None, 1)
        self.__create_rf_input_generic(expected, 'ica_zone')


if __name__ == '__main__':
    unittest.main()
