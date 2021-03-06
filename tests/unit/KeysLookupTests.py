import unittest
import copy
from parameterized import parameterized
import itertools
from datetime import date

from oasislmf.utils.coverages import COVERAGE_TYPES

from complex_model import HailAUSKeysLookup
from complex_model.Common import *
from complex_model.utils import to_bool
from tests.unit.RFBaseTest import RFBaseTestCase


OED_COVERAGES = [COVERAGE_TYPES["buildings"], COVERAGE_TYPES["contents"], COVERAGE_TYPES["other"], COVERAGE_TYPES["bi"]]
OED_STRUCTURE_COVERAGES = [COVERAGE_TYPES["buildings"], COVERAGE_TYPES["contents"], COVERAGE_TYPES["bi"]]
OED_MOTOR_COVERAGES = [COVERAGE_TYPES["buildings"]]
OED_NON_BI_COVERAGES = [COVERAGE_TYPES["buildings"], COVERAGE_TYPES["contents"]]
OED_BUILDING_CONTENTS_COVERAGES = [COVERAGE_TYPES["buildings"], COVERAGE_TYPES["contents"]]

# OCCUPANCY CODES
DEFAULT_OCCUPANCY_CODES = {}
OCCUPANCY_CODES = {}
for key in OED_OCCUPANCY_CODE:
    OCCUPANCY_CODES[key] = [y for x in OED_OCCUPANCY_CODE[key] for y in range(x["min"], x["max"] + 1)]
    DEFAULT_OCCUPANCY_CODES[key] = OED_OCCUPANCY_CODE[key][0]['min']
DEFAULT_SUPPORTED_OCCUPANCY_CODES = [DEFAULT_OCCUPANCY_CODES[key] for key in {"residential", "commercial", "industrial"}]


# CONSTRUCTION CODES
DEFAULT_CONSTRUCTION_CODES = {}
CONSTRUCTION_CODES = {}
for key in OED_CONSTRUCTION_CODE:
    CONSTRUCTION_CODES[key] = [y for x in OED_CONSTRUCTION_CODE[key] for y in range(x["min"], x["max"] + 1)]
    DEFAULT_CONSTRUCTION_CODES[key] = OED_CONSTRUCTION_CODE[key][0]['min']


OK_COVERAGES_COMMERCIAL_INDUSTRIAL = [[coverage, oc] for coverage, oc
                                      in itertools.product(OED_STRUCTURE_COVERAGES,
                                                           [DEFAULT_OCCUPANCY_CODES["commercial"],
                                                            DEFAULT_OCCUPANCY_CODES["industrial"]])]

OK_NON_BI_COVERAGES_RESIDENTIAL = [[coverage, oc] for coverage, oc
                                   in itertools.product(OED_BUILDING_CONTENTS_COVERAGES,
                                                        [DEFAULT_OCCUPANCY_CODES["residential"]])]

OK_COVERAGES_OCCUPANCY_COMBINATION = OK_COVERAGES_COMMERCIAL_INDUSTRIAL + OK_NON_BI_COVERAGES_RESIDENTIAL

FAIL_COVERAGES_OCCUPANCY_COMBINATION = [[COVERAGE_TYPES["bi"], DEFAULT_OCCUPANCY_CODES["residential"]]]

NON_MOTOR_COMMERCIAL_INDUSTRIAL = [[coverage, oc] for coverage, oc
                                   in itertools.product(OED_STRUCTURE_COVERAGES,
                                                        [DEFAULT_OCCUPANCY_CODES["commercial"],
                                                         DEFAULT_OCCUPANCY_CODES["industrial"]])]

BUILDING_CONTENTS_RESIDENTIAL = [[coverage, oc] for coverage, oc
                                 in itertools.product(OED_BUILDING_CONTENTS_COVERAGES,
                                                      [DEFAULT_OCCUPANCY_CODES["residential"]])]

OK_NON_MOTOR_COVERAGES_OCCUPANCY_COMBINATION = NON_MOTOR_COMMERCIAL_INDUSTRIAL + BUILDING_CONTENTS_RESIDENTIAL

SMV_ON = [1, 2, '1', 'true', 'True', 'TRUE']
SMV_OFF = [0, '0', 'false', 'False', 'FALSE']


class OccupancyCodeTests(RFBaseTestCase):
    """This test case provides validation that the implemented lob lookup error_code implements
    the specification as described in the documentation of the oasis integration documentation
    """
    @parameterized.expand([[cc] for cc in OCCUPANCY_CODES["unsupported"]])
    def test_get_lob_id_unsupported_occupancy(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        self.assertRaisesWithErrorCode(230, lookup._get_lob_id, {"occupancycode": cc})

    @parameterized.expand([[cc] for cc in OCCUPANCY_CODES["residential"]])
    def test_get_lob_id_residential(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        self.assertEqual(lookup._get_lob_id({"occupancycode": cc}), 1)

    @parameterized.expand([[cc] for cc in OCCUPANCY_CODES["commercial"]])
    def test_get_lob_id_commercial(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        self.assertEqual(lookup._get_lob_id({"occupancycode": cc}), 2)

    @parameterized.expand([[cc] for cc in OCCUPANCY_CODES["industrial"]])
    def test_get_lob_id_industrial(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        self.assertEqual(lookup._get_lob_id({"occupancycode": cc}), 3)


class ConstructionCodeTests(RFBaseTestCase):
    """This test case provides check for motor exposure methods
    """

    @parameterized.expand([[cc] for cc in CONSTRUCTION_CODES["motor"]])
    def test_is_motor_true(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        loc = {'locperilscovered': 'AA1', 'loc_id': 1,
               'latitude': -33.8688, 'longitude': 151.2093,
               'postalcode': 2000, 'constructioncode': cc}
        self.assertTrue(lookup._is_motor(loc))

    @parameterized.expand([[cc] for cc in CONSTRUCTION_CODES["structure"]])
    def test_is_motor_false(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        loc = {'locperilscovered': 'AA1', 'loc_id': 1,
               'latitude': -33.8688, 'longitude': 151.2093,
               'postalcode': 2000, 'constructioncode': cc}
        self.assertFalse(lookup._is_motor(loc))

    @parameterized.expand([[cc] for cc in CONSTRUCTION_CODES["unsupported"]])
    def test_unsupported_construction_codes(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        loc = {'locperilscovered': 'AA1', 'loc_id': 1,
               'latitude': -33.8688, 'longitude': 151.2093,
               'postalcode': 2000, 'constructioncode': cc}
        self.assertTrue(not lookup._is_motor(loc))


class OEDGeogSchemeTests(RFBaseTestCase):
    """This test case provides validation that the GeogScheme columns are used as described in the
    specification included in the oasis integration documentation
    """
    def test_gnaf_geogscheme(self):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        uni_exposure = lookup._add_geog_name({}, "GNAF", "GANSW123456789")
        self.assertEqual("GANSW123456789", uni_exposure["address_id"])
        self.assertEqual(EnumAddressType.GNAF.value, uni_exposure["address_type"])

    def test_pc4_geogscheme(self):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        uni_exposure = lookup._add_geog_name({}, "PC4", 2000)
        self.assertEqual(uni_exposure["med_id"], 2000)
        self.assertEqual(uni_exposure["med_type"], EnumResolution.Postcode.value)

    def test_ica_bound_geogscheme(self):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")

        uni_exposure = lookup._add_geog_name({}, "ICA", 0)
        self.assertFalse('lrg_id' in uni_exposure)

        uni_exposure = lookup._add_geog_name({}, "ICA", 50)
        self.assertFalse('lrg_id' in uni_exposure)

    @parameterized.expand([[c] for c in range(1, 50)])
    def test_ica_geogscheme(self, c):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        uni_exposure = lookup._add_geog_name({}, "ICA", c)
        self.assertEqual(uni_exposure["lrg_id"], c)
        self.assertEqual(uni_exposure["lrg_type"], EnumResolution.IcaZone.value)

    def test_cro_bound_geogscheme(self):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")

        uni_exposure = lookup._add_geog_name({}, "CRO", 0)
        self.assertFalse('zone_id' in uni_exposure)

        uni_exposure = lookup._add_geog_name({}, "CRO", 50)
        self.assertFalse('zone_id' in uni_exposure)

    @parameterized.expand([[c] for c in range(1, 50)])
    def test_cro_geogscheme(self, c):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        uni_exposure = lookup._add_geog_name({}, "CRO", c)
        self.assertEqual(uni_exposure["zone_id"], c)
        self.assertEqual(uni_exposure["zone_type"], EnumResolution.Cresta.value)


class CreateUniExposureTests(RFBaseTestCase):
    """This test ensures that create_uni_exposure method behaves as expected
    1. required field are reported as failed lookup
    2. unsupported peril
    3. cascading geolocation
    """

    @parameterized.expand([[coverage] for coverage in OED_COVERAGES])
    def test_required_fields(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")

        # missing 'locperilscovered' and 'loc_id'
        loc = {}
        self.assertRaisesWithErrorCode(101, lookup.create_uni_exposure, loc, coverage["id"])

        # missing 'loc_id'
        loc = {'locperilscovered': 'AA1'}
        self.assertRaisesWithErrorCode(102, lookup.create_uni_exposure, loc, coverage["id"])

        # missing 'locperilscovered'
        loc = {'loc_id': 'loc1'}
        self.assertRaisesWithErrorCode(101, lookup.create_uni_exposure, loc, coverage["id"])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_unsupported_values(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': -33.8688, 'longitude': 151.2093,
                       'postalcode': 2000, 'occupancycode': oc}

        # unsupported peril
        loc = copy.deepcopy(default_loc)
        loc.update({'locperilscovered': 'QQ1'})
        self.assertRaisesWithErrorCode(122, lookup.create_uni_exposure, loc, coverage['id'])

        # unsupported lob_id
        loc = copy.deepcopy(default_loc)
        loc.update({'occupancycode': 0})
        self.assertRaisesWithErrorCode(230, lookup.create_uni_exposure, loc, coverage['id'])
        loc = copy.deepcopy(default_loc)
        loc.update({'occupancycode': 'a'})
        self.assertRaisesWithErrorCode(123, lookup.create_uni_exposure, loc, coverage['id'])

        # unsupported year_built
        loc = copy.deepcopy(default_loc)
        loc.update({"yearbuilt": 0})
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(0, exposure["props"]["YearBuilt"])
        loc.update({"yearbuilt": 'a'})
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertFalse('YearBuilt' in exposure["props"])
        loc.update({"yearbuilt": 2001})
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(2001, exposure["props"]["YearBuilt"])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_level(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        lookup._supported_gnaf = ['GANSW123456789']
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': "GNAF", 'geogname1': "GANSW123456789", 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual("GANSW123456789", exposure['address_id'])
        self.assertEqual(EnumAddressType.GNAF.value, exposure['address_type'])
        self.assertEqual(EnumResolution.Address.value, exposure['best_res'])

        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)
        self.assertFalse('state' in exposure and exposure['state'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_level_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        lookup._supported_gnaf = ['GANSW123456789']
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': "GNAF", 'geogname1': "GANSW123456789", 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_state(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        lookup._supported_gnaf = ['GANSW123456789']
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': "GNAF", 'geogname1': "GANSW123456789",
                       'areacode': 'nsw', 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual("GANSW123456789", exposure['address_id'])
        self.assertEqual(EnumAddressType.GNAF.value, exposure['address_type'])
        self.assertEqual(EnumResolution.Address.value, exposure['best_res'])
        self.assertEqual('nsw', exposure['state'].lower())

        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_state_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        lookup._supported_gnaf = ['GANSW123456789']
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': "GNAF", 'geogname1': "GANSW123456789",
                       'areacode': 'nsw', 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_latlon_level(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)
        self.assertFalse('state' in exposure and exposure['state'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_latlon_level_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_latlon(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        lookup._supported_gnaf = ['GANSW123456789']
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'GNAF', 'geogname1': 'GANSW123456789',
                       'latitude': latitude, 'longitude': longitude, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumAddressType.GNAF.value, exposure['address_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_latlon_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'GNAF', 'geogname1': 'GANSW123456789',
                       'latitude': latitude, 'longitude': longitude, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_postcode_level(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'postalcode': 2000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(2000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_postcode_level_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'postalcode': 2000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_pc4_level(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': "PC4", "geogname1": 2000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(2000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_pc4_level_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': "PC4", "geogname1": 2000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_postcode(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        lookup._supported_gnaf = ['GANSW123456789']
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'GNAF', 'geogname1': 'GANSW123456789',
                       'postalcode': 2000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumAddressType.GNAF.value, exposure['address_type'])
        self.assertEqual(2000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.Address.value, exposure['best_res'])

        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_postcode_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'GNAF', 'geogname1': 'GANSW123456789',
                       'postalcode': 2000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_latlon_postcode(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'postalcode': 2000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual(2000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_latlon_postcode_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'postalcode': 2000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_latlon_pc4(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'PC4', 'geogname1': 2000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual(2000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_latlon_pc4_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'PC4', 'geogname1': 2000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_latlon_postcode_pc4(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'PC4', 'geogname1': 2000,
                       'postalcode': 4000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual(4000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_latlon_postcode_pc4_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'PC4', 'geogname1': 2000,
                       'postalcode': 4000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_latlon_postcode_pc4(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        lookup._supported_gnaf = ['GANSW123456789']
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme2': 'GNAF', 'geogname2': 'GANSW123456789',
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'PC4', 'geogname1': 2000,
                       'postalcode': 4000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumAddressType.GNAF.value, exposure['address_type'])
        self.assertEqual(4000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_latlon_postcode_pc4_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme2': 'GNAF', 'geogname2': 'GANSW123456789',
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'PC4', 'geogname1': 2000,
                       'postalcode': 4000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_cresta_level(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'CRO', 'geogname1': 49, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(49, exposure['zone_id'])
        self.assertEqual(EnumResolution.Cresta.value, exposure['zone_type'])
        self.assertEqual(EnumResolution.Cresta.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_cresta_level_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'CRO', 'geogname1': 49, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_cresta(self, coverage, occupancy_code):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        lookup._supported_gnaf = ['GANSW123456789']
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'GNAF', 'geogname1': 'GANSW123456789',
                       'geogscheme2': 'CRO', 'geogname2': 49,
                       "occupancycode": occupancy_code}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumAddressType.GNAF.value, exposure['address_type'])
        self.assertEqual(49, exposure['zone_id'])
        self.assertEqual(EnumResolution.Cresta.value, exposure['zone_type'])
        self.assertEqual(EnumResolution.Address.value, exposure['best_res'])

        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_cresta_fail(self, coverage, occupancy_code):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'GNAF', 'geogname1': 'GANSW123456789',
                       'geogscheme2': 'CRO', 'geogname2': 49,
                       "occupancycode": occupancy_code}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_latlon_cresta(self, coverage, occupancy_code):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'CRO', 'geogname1': 49,
                       "occupancycode": occupancy_code}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual(49, exposure['zone_id'])
        self.assertEqual(EnumResolution.Cresta.value, exposure['zone_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_latlon_cresta_fail(self, coverage, occupancy_code):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'CRO', 'geogname1': 49,
                       "occupancycode": occupancy_code}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_postcode_cresta(self, coverage, occupancy_code):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'CRO', 'geogname1': 49,
                       'postalcode': 4000,
                       "occupancycode": occupancy_code}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(49, exposure['zone_id'])
        self.assertEqual(EnumResolution.Cresta.value, exposure['zone_type'])
        self.assertEqual(4000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_postcode_cresta_fail(self, coverage, occupancy_code):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'CRO', 'geogname1': 49,
                       'postalcode': 4000,
                       "occupancycode": occupancy_code}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_latlon_postcode_cresta(self, coverage, occupancy_code):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        lookup._supported_gnaf = ['GANSW123456789']
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'CRO', 'geogname1': 49,
                       'geogscheme2': 'GNAF', 'geogname2': 'GANSW123456789',
                       'postalcode': 4000,
                       "occupancycode": occupancy_code}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumAddressType.GNAF.value, exposure['address_type'])
        self.assertEqual(49, exposure['zone_id'])
        self.assertEqual(EnumResolution.Cresta.value, exposure['zone_type'])
        self.assertEqual(4000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_latlon_postcode_cresta_fail(self, coverage, occupancy_code):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'CRO', 'geogname1': 49,
                       'geogscheme2': 'GNAF', 'geogname2': 'GANSW123456789',
                       'postalcode': 4000,
                       "occupancycode": occupancy_code}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_ica_zone_level(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'ICA', 'geogname1': 49, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(49, exposure['lrg_id'])
        self.assertEqual(EnumResolution.IcaZone.value, exposure['lrg_type'])
        self.assertEqual(EnumResolution.IcaZone.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_ica_zone_level_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'ICA', 'geogname1': 49, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_ica_zone_cresta_level(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'ICA', 'geogname1': 49,
                       'geogscheme2': 'CRO', 'geogname2': 2, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(49, exposure['lrg_id'])
        self.assertEqual(EnumResolution.IcaZone.value, exposure['lrg_type'])
        self.assertEqual(2, exposure['zone_id'])
        self.assertEqual(EnumResolution.Cresta.value, exposure['zone_type'])
        self.assertEqual(EnumResolution.Cresta.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_ica_zone_cresta_level_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'ICA', 'geogname1': 49,
                       'geogscheme2': 'CRO', 'geogname2': 2, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_ica_zone(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        lookup._supported_gnaf = ['GANSW123456789']
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'GNAF', 'geogname1': 'GANSW123456789',
                       'geogscheme2': 'ICA', 'geogname2': 49, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumAddressType.GNAF.value, exposure['address_type'])
        self.assertEqual(49, exposure['lrg_id'])
        self.assertEqual(EnumResolution.IcaZone.value, exposure['lrg_type'])
        self.assertEqual(EnumResolution.Address.value, exposure['best_res'])

        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_ica_zone_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'GNAF', 'geogname1': 'GANSW123456789',
                       'geogscheme2': 'ICA', 'geogname2': 49, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_latlon_ica_zone(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'ICA', 'geogname1': 49, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual(49, exposure['lrg_id'])
        self.assertEqual(EnumResolution.IcaZone.value, exposure['lrg_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_latlon_ica_zone_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'ICA', 'geogname1': 49, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_postcode_ica_zone(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'ICA', 'geogname1': 49,
                       'postalcode': 4000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(49, exposure['lrg_id'])
        self.assertEqual(EnumResolution.IcaZone.value, exposure['lrg_type'])
        self.assertEqual(4000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['best_res'])

        self.assertFalse('address_id' in exposure and exposure['address_id'] is not None)
        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_postcode_ica_zone_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'ICA', 'geogname1': 49,
                       'postalcode': 4000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_latlon_postcode_ica_zone(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        lookup._supported_gnaf = ['GANSW123456789']
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'ICA', 'geogname1': 49,
                       'geogscheme2': 'GNAF', 'geogname2': 'GANSW123456789',
                       'postalcode': 4000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumAddressType.GNAF.value, exposure['address_type'])
        self.assertEqual(49, exposure['lrg_id'])
        self.assertEqual(EnumResolution.IcaZone.value, exposure['lrg_type'])
        self.assertEqual(4000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_latlon_postcode_ica_zone_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'ICA', 'geogname1': 49,
                       'geogscheme2': 'GNAF', 'geogname2': 'GANSW123456789',
                       'postalcode': 4000, 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand(OK_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_latlon_postcode_cresta_ica_zone_state(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        lookup._supported_gnaf = ['GANSW123456789']
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'ICA', 'geogname1': 49,
                       'geogscheme2': 'GNAF', 'geogname2': 'GANSW123456789',
                       'geogscheme3': 'CRO', 'geogname3': 2,
                       'postalcode': 4000, 'areacode': 'nsw', 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumAddressType.GNAF.value, exposure['address_type'])
        self.assertEqual(49, exposure['lrg_id'])
        self.assertEqual(EnumResolution.IcaZone.value, exposure['lrg_type'])
        self.assertEqual(2, exposure['zone_id'])
        self.assertEqual(EnumResolution.Cresta.value, exposure['zone_type'])
        self.assertEqual(4000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])
        self.assertEqual('nsw', exposure['state'].lower())

    @parameterized.expand(FAIL_COVERAGES_OCCUPANCY_COMBINATION)
    def test_address_latlon_postcode_cresta_ica_zone_state_fail(self, coverage, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'ICA', 'geogname1': 49,
                       'geogscheme2': 'GNAF', 'geogname2': 'GANSW123456789',
                       'geogscheme3': 'CRO', 'geogname3': 2,
                       'postalcode': 4000, 'areacode': 'nsw', 'occupancycode': oc}

        loc = copy.deepcopy(default_loc)
        self.assertRaisesWithErrorCode(151, lookup.create_uni_exposure, loc, coverage['id'])

    @parameterized.expand([[cc, oc] for cc in CONSTRUCTION_CODES["motor"] for oc in DEFAULT_SUPPORTED_OCCUPANCY_CODES])
    def test_motor_exposure(self, cc, oc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'postalcode': 2000}

        loc = copy.deepcopy(default_loc)
        loc.update({'constructioncode': cc, 'occupancycode': oc})
        exposure = lookup.create_uni_exposure(loc, COVERAGE_TYPES['buildings']['id'])
        self.assertEqual(EnumCover.Motor.value, exposure['cover_id'])


class CreateUniExposureOEDFieldsTests(RFBaseTestCase):
    """This test ensures that YearBuilt is parsed properly from OED

    """
    @parameterized.expand([[year] for year in range(date.today().year + 1)])
    def test_year_built_values(self, year):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': -33.8688, 'longitude': 151.2093,
                       'postalcode': 2000, 'yearbuilt': year}

        # unsupported peril
        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, COVERAGE_TYPES['buildings']['id'])
        self.assertEqual(year, exposure["props"]["YearBuilt"])

    def test_static_motor_default(self):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': -33.8688, 'longitude': 151.2093,
                       'postalcode': 2000}

        # unsupported peril
        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, COVERAGE_TYPES['buildings']['id'])
        self.assertTrue("StaticMotor" not in exposure["props"])

    @parameterized.expand([[smv] for smv in SMV_ON])
    def test_static_motor_on(self, smv):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': -33.8688, 'longitude': 151.2093,
                       'postalcode': 2000, 'staticmotorvehicle': smv}

        # unsupported peril
        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, COVERAGE_TYPES['buildings']['id'])
        self.assertEqual(True, exposure["props"]["StaticMotor"])

    @parameterized.expand([[smv] for smv in SMV_OFF])
    def test_static_motor_off(self, smv):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': -33.8688, 'longitude': 151.2093,
                       'postalcode': 2000, 'staticmotorvehicle': smv}

        # unsupported peril
        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, COVERAGE_TYPES['buildings']['id'])
        self.assertEqual(False, exposure["props"]["StaticMotor"])

    @parameterized.expand([[smv] for smv in ['a', None]])
    def test_static_motor_bad_values(self, smv):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': -33.8688, 'longitude': 151.2093,
                       'postalcode': 2000, 'staticmotorvehicle': smv}

        # unsupported peril
        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, COVERAGE_TYPES['buildings']['id'])
        self.assertTrue("StaticMotor" not in exposure["props"])

    @parameterized.expand([[smv, cc] for cc in CONSTRUCTION_CODES["motor"] for smv in SMV_OFF + SMV_ON])
    def test_static_motor_marine(self, smv, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': -33.8688, 'longitude': 151.2093,
                       'postalcode': 2000, 'constructioncode': cc, "staticmotorvehicle": smv}

        # unsupported peril
        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, COVERAGE_TYPES['buildings']['id'])
        is_marine = lookup._check_in_group(loc, 'motor_marine', lookup._codes_mapping["construction"])
        if is_marine:
            self.assertTrue(exposure["props"]["StaticMotor"])
        else:
            self.assertEqual(to_bool(smv), exposure["props"]["StaticMotor"])


if __name__ == '__main__':
    unittest.main()
