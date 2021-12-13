import unittest
import os
import pandas as pd
from parameterized import parameterized

from tests.unit.RFBaseTest import RFBaseTestCase
from complex_model import PostcodeLookup

TEST_DIR = os.path.dirname(__file__)
TEST_KEYS_DATA_DIR = os.path.join(TEST_DIR, 'data', 'keys_data')
TEST_INPUT_DIR = os.path.join(TEST_DIR, 'data', 'input', 'postcode_lookup')
PL = PostcodeLookup(TEST_KEYS_DATA_DIR)

locations_file = os.path.join(TEST_INPUT_DIR, 'locations.csv')
with open(locations_file, 'r') as f:
    locations = pd.read_csv(f)


class PostcodeLookupTests(RFBaseTestCase):
    """This test case provides validation for the postcode lookup method
    """
    @parameterized.expand([[test_loc['postcode'], test_loc['longitude'], test_loc['latitude']]
                           for _, test_loc in locations.iterrows()])
    def test_get_postcode(self, postcode, longitude, latitude):
        looked_postcode = PL.get_postcode(longitude, latitude)
        self.assertEqual(postcode, looked_postcode, f"failed for {latitude},{longitude}")

    def test_get_postcode_zero(self):
        looked_postcode = PL.get_postcode(0, 0)
        self.assertEqual(None, looked_postcode)

        looked_postcode = PL.get_postcode(None, 0)
        self.assertEqual(None, looked_postcode)

        looked_postcode = PL.get_postcode(0, None)
        self.assertEqual(None, looked_postcode)

        looked_postcode = PL.get_postcode(None, None)
        self.assertEqual(None, looked_postcode)


if __name__ == '__main__':
    unittest.main()
