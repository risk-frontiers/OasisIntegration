import unittest
import copy
from parameterized import parameterized

from oasislmf.utils.coverages import COVERAGE_TYPES

from complex_model import HailAUSKeysLookup
from complex_model.Common import *
from tests.unit.RFBaseTest import RFBaseTestCase

COVERAGES = [COVERAGE_TYPES["buildings"], COVERAGE_TYPES["contents"], COVERAGE_TYPES["other"], COVERAGE_TYPES["bi"]]


class OccupancyCodeTests(RFBaseTestCase):
    """This test case provides validation that the implemented lob lookup error_code implements
    the specification as described in the documentation of the oasis integration documentation
    """
    def test_get_lob_id_zero_occupancy(self):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        self.assertRaisesWithErrorCode(123, lookup._get_lob_id, {"occupancycode": 0})

    @parameterized.expand([[cc] for cc in range(1250, 4000)])
    def test_get_lob_id_unsupported_occupancy(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        self.assertRaisesWithErrorCode(123, lookup._get_lob_id, {"occupancycode": cc})

    @parameterized.expand([[1000]] + [[cc] for cc in range(1050, 1100)])
    def test_get_lob_id_residential(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        self.assertEqual(lookup._get_lob_id({"occupancycode": cc}), 1)

    @parameterized.expand([[cc] for cc in range(1100, 1150)] + [[cc] for cc in range(1200, 1250)])
    def test_get_lob_id_commercial(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        self.assertEqual(lookup._get_lob_id({"occupancycode": cc}), 2)

    @parameterized.expand([[cc] for cc in range(1150, 1200)])
    def test_get_lob_id_industrial(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        self.assertEqual(lookup._get_lob_id({"occupancycode": cc}), 3)


class MotorExposureTests(RFBaseTestCase):
    """This test case provides check for motor exposure methods
    """

    @parameterized.expand([[cc] for cc in range(5850, 5950)])
    def test_is_motor_true(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                   'latitude': -33.8688, 'longitude': 151.2093,
                   'postalcode': 2000, 'constructioncode': cc}
        self.assertTrue(lookup._is_motor(loc))

    def test_is_motor_false(self):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        loc = {'locperilscovered': 'AA1', 'loc_id': 1,
               'latitude': -33.8688, 'longitude': 151.2093,
               'postalcode': 2000}
        self.assertFalse(lookup._is_motor(loc))


class OEDGeogSchemeTests(RFBaseTestCase):
    """This test case provides validation that the GeogScheme columns are used as described in the
    specification included in the oasis integration documentation
    """
    def test_gnaf_geogscheme(self):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        uni_exposure = lookup._add_geog_name({}, "GNAF", "GANSW123456789")
        self.assertEqual(uni_exposure["address_id"], "GANSW123456789")
        self.assertEqual(uni_exposure["address_type"], EnumResolution.Address.value)

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_unsupported_values(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': -33.8688, 'longitude': 151.2093,
                       'postalcode': 2000}

        # unsupported peril
        loc = copy.deepcopy(default_loc)
        loc.update({'locperilscovered': 'QQ1'})
        self.assertRaisesWithErrorCode(122, lookup.create_uni_exposure, loc, coverage['id'])

        # unsupported lob_id
        loc = copy.deepcopy(default_loc)
        loc.update({'occupancycode': 0})
        self.assertRaisesWithErrorCode(123, lookup.create_uni_exposure, loc, coverage['id'])
        loc = copy.deepcopy(default_loc)
        loc.update({'occupancycode': 'a'})
        self.assertRaisesWithErrorCode(124, lookup.create_uni_exposure, loc, coverage['id'])

        # unsupported year_built
        loc = copy.deepcopy(default_loc)
        loc.update({"yearbuilt": 0})
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(0, exposure["props"]["YearBuilt"])
        loc.update({"yearbuilt": 'a'})
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(0, exposure["props"]["YearBuilt"])
        loc.update({"yearbuilt": 2001})
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(2001, exposure["props"]["YearBuilt"])

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_address_level(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': "GNAF", 'geogname1': "GANSW123456789"}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual("GANSW123456789", exposure['address_id'])
        self.assertEqual(EnumResolution.Address.value, exposure['address_type'])
        self.assertEqual(EnumResolution.Address.value, exposure['best_res'])

        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)
        self.assertFalse('state' in exposure and exposure['state'] is not None)

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_address_state(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': "GNAF", 'geogname1': "GANSW123456789",
                       'areacode': 'au'}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual("GANSW123456789", exposure['address_id'])
        self.assertEqual(EnumResolution.Address.value, exposure['address_type'])
        self.assertEqual(EnumResolution.Address.value, exposure['best_res'])
        self.assertEqual('au', exposure['state'])

        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_latlon_level(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_address_latlon(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'GNAF', 'geogname1': 'GANSW123456789',
                       'latitude': latitude, 'longitude': longitude}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumResolution.Address.value, exposure['address_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_postcode_level(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'postalcode': 2000}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_pc4_level(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': "PC4", "geogname1": 2000}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_address_postcode(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'GNAF', 'geogname1': 'GANSW123456789',
                       'postalcode': 2000}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumResolution.Address.value, exposure['address_type'])
        self.assertEqual(2000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.Address.value, exposure['best_res'])

        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_latlon_postcode(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'postalcode': 2000}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_latlon_pc4(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'PC4', 'geogname1': 2000}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_latlon_postcode_pc4(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'PC4', 'geogname1': 2000,
                       'postalcode': 4000}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_address_latlon_postcode_pc4(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme2': 'GNAF', 'geogname2': 'GANSW123456789',
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'PC4', 'geogname1': 2000,
                       'postalcode': 4000}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumResolution.Address.value, exposure['address_type'])
        self.assertEqual(4000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_cresta_level(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'CRO', 'geogname1': 49}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_address_cresta(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'GNAF', 'geogname1': 'GANSW123456789',
                       'geogscheme2': 'CRO', 'geogname2': 49}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumResolution.Address.value, exposure['address_type'])
        self.assertEqual(49, exposure['zone_id'])
        self.assertEqual(EnumResolution.Cresta.value, exposure['zone_type'])
        self.assertEqual(EnumResolution.Address.value, exposure['best_res'])

        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_latlon_cresta(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'CRO', 'geogname1': 49}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_postcode_cresta(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'CRO', 'geogname1': 49,
                       'postalcode': 4000}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_address_latlon_postcode_cresta(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'CRO', 'geogname1': 49,
                       'geogscheme2': 'GNAF', 'geogname2': 'GANSW123456789',
                       'postalcode': 4000}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumResolution.Address.value, exposure['address_type'])
        self.assertEqual(49, exposure['zone_id'])
        self.assertEqual(EnumResolution.Cresta.value, exposure['zone_type'])
        self.assertEqual(4000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('lrg_id' in exposure and exposure['lrg_id'] is not None)

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_ica_zone_level(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'ICA', 'geogname1': 49}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_ica_zone_cresta_level(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'ICA', 'geogname1': 49,
                       'geogscheme2': 'CRO', 'geogname2': 2}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_address_ica_zone(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'GNAF', 'geogname1': 'GANSW123456789',
                       'geogscheme2': 'ICA', 'geogname2': 49}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumResolution.Address.value, exposure['address_type'])
        self.assertEqual(49, exposure['lrg_id'])
        self.assertEqual(EnumResolution.IcaZone.value, exposure['lrg_type'])
        self.assertEqual(EnumResolution.Address.value, exposure['best_res'])

        self.assertFalse('latitude' in exposure and exposure['latitude'] is not None)
        self.assertFalse('longitude' in exposure and exposure['longitude'] is not None)
        self.assertFalse('med_id' in exposure and exposure['med_id'] is not None)
        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_latlon_ica_zone(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'ICA', 'geogname1': 49}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_postcode_ica_zone(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'geogscheme1': 'ICA', 'geogname1': 49,
                       'postalcode': 4000}

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

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_address_latlon_postcode_ica_zone(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'ICA', 'geogname1': 49,
                       'geogscheme2': 'GNAF', 'geogname2': 'GANSW123456789',
                       'postalcode': 4000}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumResolution.Address.value, exposure['address_type'])
        self.assertEqual(49, exposure['lrg_id'])
        self.assertEqual(EnumResolution.IcaZone.value, exposure['lrg_type'])
        self.assertEqual(4000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])

        self.assertFalse('zone_id' in exposure and exposure['zone_id'] is not None)

    @parameterized.expand([[coverage] for coverage in COVERAGES])
    def test_address_latlon_postcode_cresta_ica_zone_state(self, coverage):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        latitude = -33.8688
        longitude = 151.2093
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'latitude': latitude, 'longitude': longitude,
                       'geogscheme1': 'ICA', 'geogname1': 49,
                       'geogscheme2': 'GNAF', 'geogname2': 'GANSW123456789',
                       'geogscheme3': 'CRO', 'geogname3': 2,
                       'postalcode': 4000, 'areacode': 'au'}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, coverage['id'])
        self.assertEqual(latitude, exposure['latitude'])
        self.assertEqual(longitude, exposure['longitude'])
        self.assertEqual('GANSW123456789', exposure['address_id'])
        self.assertEqual(EnumResolution.Address.value, exposure['address_type'])
        self.assertEqual(49, exposure['lrg_id'])
        self.assertEqual(EnumResolution.IcaZone.value, exposure['lrg_type'])
        self.assertEqual(2, exposure['zone_id'])
        self.assertEqual(EnumResolution.Cresta.value, exposure['zone_type'])
        self.assertEqual(4000, exposure['med_id'])
        self.assertEqual(EnumResolution.Postcode.value, exposure['med_type'])
        self.assertEqual(EnumResolution.LatLong.value, exposure['best_res'])
        self.assertEqual('au', exposure['state'])

    @parameterized.expand([[cc] for cc in range(5850, 5950)])
    def test_motor_exposure_motor(self, cc):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'postalcode': 2000}

        loc = copy.deepcopy(default_loc)
        loc.update({'constructioncode': cc})
        exposure = lookup.create_uni_exposure(loc, COVERAGE_TYPES['other']['id'])
        self.assertEqual(EnumCover.Motor.value, exposure['cover_id'])

    def test_motor_exposure_building(self):
        lookup = HailAUSKeysLookup(keys_data_directory=None, model_name="hailAus")
        default_loc = {'locperilscovered': 'AA1', 'loc_id': 1,
                       'postalcode': 2000}

        loc = copy.deepcopy(default_loc)
        exposure = lookup.create_uni_exposure(loc, COVERAGE_TYPES['other']['id'])
        self.assertEqual(EnumCover.Building.value, exposure['cover_id'])


if __name__ == '__main__':
    unittest.main()
