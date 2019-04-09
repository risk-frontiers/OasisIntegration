import itertools
import json

import oasislmf.utils.coverage
from oasislmf.utils.metadata import (
    OASIS_KEYS_SC,
    OASIS_KEYS_FL,
    OASIS_KEYS_NM,
    OASIS_KEYS_STATUS)
from oasislmf.model_preparation.lookup import OasisBaseKeysLookup
from complex_model.PostcodeLookup import PostcodeLookup
from complex_model.RFException import LocationLookupException
from complex_model.Common import *


class HailAUSKeysLookup(OasisBaseKeysLookup):
    def __init__(self,
                 keys_data_directory=None,
                 supplier=None,
                 model_name=None,
                 model_version=None):
        self.keys_file_dir = keys_data_directory
        self._coverage_types = [
            oasislmf.utils.coverage.BUILDING_COVERAGE_CODE,  # 1
            oasislmf.utils.coverage.CONTENTS_COVERAGE_CODE,  #
            oasislmf.utils.coverage.TIME_COVERAGE_CODE,
            oasislmf.utils.coverage.OTHER_STRUCTURES_COVERAGE_CODE]
        self._peril_id = None
        if model_name is not None and model_name.lower() in PerilSet.keys():
            self._peril_id = PerilSet[model_name.lower()]['OED_ID']
        if self.keys_file_dir:
            self._postcode_lookup = PostcodeLookup(keys_file_dir=self.keys_file_dir)

    def _get_lob_id(self, record):
        """This transforms the occupancy code into Multi-Peril Workbench specified line of business"""
        if 'occupancycode' not in record:
            return 1  # residential: this is the default behaviour when this field is missing in the workbench
        if record['occupancycode'] == 1000 or 1050 <= record['occupancycode'] <= 1099:
            return 1  # residential
        elif 1100 <= record['occupancycode'] <= 1149:
            return 2  # commercial
        elif 1150 <= record['occupancycode'] <= 1199:
            return 3  # industrial
        else:
            raise LocationLookupException("Unsupported occupancy code " + str(record['occupancycode']))

    def _validate(self, uni_exposure):
        """This validates the uni_exposure as per the Multi-Peril Workbench specification
                1. we ignore a location that has no postcode if the peril is Hail
                2. we ignore location that has not geographical specification (address, lat/lon, cresta, ica_zone)

        :param uni_exposure:
        :return: validated uni_exposure
        """
        if uni_exposure['address_id'] is None and uni_exposure['med_id'] is None and self._peril_id is not None \
                and self._peril_id & OEDPeril.Hail.value > 0:
            raise LocationLookupException("Cannot find postcode for location " + str(uni_exposure['loc_id']) +
                                          ". Postcode is required for " + str(OEDPeril.Hail))

        if not ((uni_exposure['latitude'] and uni_exposure['longitude']) or uni_exposure['address_id'] or
                uni_exposure['med_id'] or uni_exposure['zone_id'] or uni_exposure['lrg_id']):
            raise LocationLookupException("A location must have at least a Cresta, Ica Zone, Postalcode, Lat/Lon "
                                          "or address coordinate")

        return uni_exposure

    def create_uni_exposure(self, loc, coverage_type):
        """This creates a uni_exposure object from an oasis loc object.
        The u_exposure table contains the following columns:

        loc_id, latitude, longitude, address_type, address_id, best_res, country_code, state, zone_type, zone_id,
        catchment_type, catchment_id, lrg_type, lrg_id, med_type, med_id, fine_type, fine_id, lob_id, props, modelled,
        origin_file_line

        :param loc: a row from a OED portfolio
        :param coverage_type: is a either building [1], contents [3], other [3] (motor) or business interruption [4]
        :return: a uni_exposure object as per the Multi-Peril Workbench specification
        """
        peril_covered = int(loc['locperilscovered']) \
            if 'locperilscovered' in loc and loc['locperilscovered'] is not None else 0  # todo: check that this is ok
        if peril_covered > 0 and not self._peril_id & peril_covered > 0:
            raise LocationLookupException('Location not covered for ' + str(oed_to_rf_peril(self._peril_id)))

        uni_exposure = dict()
        uni_exposure['origin_file_line'] = int(loc['locnumber'])
        uni_exposure['lob_id'] = self._get_lob_id(loc)
        uni_exposure['cover_id'] = oed_to_rf_coverage(coverage_type)

        # ica zone
        try:
            uni_exposure['lrg_id'] = int(loc['locuserdef2']) if 'locuserdef2' in loc else None
            uni_exposure['lrg_type'] = EnumResolution.IcaZone.value \
                if uni_exposure['lrg_id'] and uni_exposure['lrg_id'] > 0 else None
            if uni_exposure['lrg_id']:
                uni_exposure['best_res'] = EnumResolution.IcaZone.value
        except (ValueError, TypeError):
            uni_exposure['lrg_id'] = None

        # cresta
        try:
            uni_exposure['zone_id'] = int(loc['lowrescresta']) if 'lowrescresta' in loc else None
            uni_exposure['zone_type'] = EnumResolution.Cresta.value \
                if uni_exposure['zone_id'] and uni_exposure['zone_id'] > 0 else None
            if uni_exposure['zone_id']:
                uni_exposure['best_res'] = EnumResolution.Cresta.value
        except (ValueError, TypeError):
            uni_exposure['zone_id'] = None

        # postcode
        try:
            uni_exposure['med_id'] = int(loc['postalcode']) if 'postalcode' in loc else None
            uni_exposure['med_type'] = EnumResolution.Postcode.value \
                if uni_exposure['med_id'] and uni_exposure['med_id'] > 0 else None
            if uni_exposure['med_id']:
                uni_exposure['best_res'] = EnumResolution.Postcode.value
        except (ValueError, TypeError):
            uni_exposure['med_id'] = None

        if 'locnumber' not in loc:
            raise LocationLookupException("Location Number is required but is missing in the OED file")

        # address
        try:
            uni_exposure['address_id'] = loc['locuserdef1'] if 'locuserdef1' in loc else None
            uni_exposure['address_type'] = EnumResolution.Address.value if uni_exposure['address_id'] else None
            if uni_exposure['address_id']:
                uni_exposure['best_res'] = EnumResolution.Address.value
        except (ValueError, TypeError):
            uni_exposure['address_id'] = None

        # lat/lon
        uni_exposure['latitude'] = None
        uni_exposure['longitude'] = None
        if loc['longitude'] and loc['latitude']:
            if AU_BOUNDING_BOX['MIN'][0] <= loc["longitude"] <= AU_BOUNDING_BOX['MAX'][0] \
                    and AU_BOUNDING_BOX['MIN'][1] <= loc["latitude"] <= AU_BOUNDING_BOX['MAX'][1]:
                uni_exposure['latitude'] = loc['latitude']
                uni_exposure['longitude'] = loc['longitude']
                uni_exposure['best_res'] = EnumResolution.LatLong.value
                if uni_exposure['med_id'] is None and self._postcode_lookup:
                    uni_exposure['med_id'] = self._postcode_lookup.get_postcode(loc["longitude"], loc["latitude"])
                if uni_exposure['lrg_id'] is None:
                    pass  # todo: cresta lookup for lat/lon not required for hail at the moment
            else:
                raise LocationLookupException("Location is not in Australia")

        uni_exposure['loc_id'] = str(loc['locnumber'])

        # todo: fix when implementing quake nz
        uni_exposure['country_code'] = str(loc["countrycode"]).lower() if 'countrycode' in loc else "au"
        uni_exposure['state'] = str(loc['areacode']) if 'areacode' in loc else None

        # uni_exposure['catchment_type'] # todo: when implementing flood
        # uni_exposure['catchment_id']

        # uni_exposure['fine_type']
        # uni_exposure['fine_id']

        year_built = int(loc['yearbuilt']) if 'yearbuilt' in loc and loc['yearbuilt'] else 0
        uni_exposure['props'] = {"YearBuilt": year_built}

        # uni_exposure['modelled']

        return self._validate(uni_exposure)

    def process_location(self, loc, coverage_type):
        try:
            uni_exposure = self.create_uni_exposure(loc, coverage_type)
            return {
                'locnumber': loc['locnumber'],
                'peril_id': self._peril_id,
                'coverage_type': coverage_type,
                'model_data': json.dumps(uni_exposure),
                'status': OASIS_KEYS_SC,
                'message': "OK"
            }
        except LocationLookupException as e:
            return {
                'locnumber': loc['locnumber'],
                'peril_id': self._peril_id,
                'coverage_type': coverage_type,
                'status': OASIS_KEYS_FL,
                'message': str(e)
            }

    def process_locations(self, locs):
        locs_seq = (loc for _, loc in locs.iterrows())
        for loc, coverage_type in \
                itertools.product(locs_seq, self._coverage_types):
            yield self.process_location(loc, coverage_type)


if __name__ == "__main__":
    cl = HailAUSKeysLookup(keys_data_directory="/hadoop/oasis/keys_data", model_name="hailAus")
    test_loc = {'locnumber': 1, 'latitude': -33.8688, 'longitude': 151.2093}
    print(cl.process_location(test_loc, 1))
