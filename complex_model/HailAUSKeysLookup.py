import itertools
import json

import oasislmf.utils.coverage
from oasislmf.utils.metadata import (
    OASIS_KEYS_SC,
    OASIS_KEYS_FL,
    OASIS_KEYS_NM,
    OASIS_KEYS_STATUS)
from oasislmf.model_preparation.lookup import OasisBaseKeysLookup
from .PostcodeLookup import PostcodeLookup
from .OasisToRF import EnumResolution
from .RFException import LocationLookupException
from .RFPerils import PerilSet, OEDPeril


class HailAUSKeysLookup(OasisBaseKeysLookup):
    def __init__(self,
                 keys_data_directory=None,
                 supplier=None,
                 model_name=None,
                 model_version=None):
        self.keys_file_dir = keys_data_directory
        self._coverage_types = [
            oasislmf.utils.coverage.BUILDING_COVERAGE_CODE,
            oasislmf.utils.coverage.CONTENTS_COVERAGE_CODE,
            oasislmf.utils.coverage.TIME_COVERAGE_CODE,
            oasislmf.utils.coverage.OTHER_STRUCTURES_COVERAGE_CODE]
        self._peril_id = None
        if model_name is not None and model_name.lower() in PerilSet.keys():
            self._peril_id = PerilSet[model_name.lower()]['OED_ID']
        if self.keys_file_dir:
            self._postcode_lookup = PostcodeLookup(keys_file_dir=self.keys_file_dir)

    def _get_lob_id(self, record):
        if 'occupancycode' not in record:
            return 1  # residential: this is the default behaviour when this field is missing in the workbench
        if 1050 <= record['occupancycode'] <= 1099:
            return 1  # residential
        elif 1100 <= record['occupancycode'] <= 1149:
            return 2  # commercial
        elif 1150 <= record['occupancycode'] <= 1199:
            return 3  # industrial
        else:
            return None

    def create_uni_exposure(self, loc, coverage_type):
        uni_exposure = dict()
        uni_exposure['origin_file_line'] = int(loc['locnumber'])
        uni_exposure['lob_id'] = self._get_lob_id(loc)
        uni_exposure['cover_id'] = coverage_type

        try:
            uni_exposure['lrg_id'] = int(loc['lowrescresta']) if 'lowrescresta' in loc else None
            uni_exposure['lrg_type'] = 2 if uni_exposure['lrg_id'] else None
            if uni_exposure['lrg_id']:
                uni_exposure['best_res'] = EnumResolution.Cresta.value
        except ValueError:
            uni_exposure['lrg_id'] = None

        try:
            uni_exposure['med_id'] = int(loc['postalcode']) if 'postalcode' in loc else None
            uni_exposure['med_type'] = 1 if uni_exposure['med_id'] and uni_exposure['med_id'] > 0 else None
            if uni_exposure['med_id']:
                uni_exposure['best_res'] = EnumResolution.Postcode.value
        except ValueError:
            uni_exposure['med_id'] = None

        if 'locnumber' not in loc:
            raise LocationLookupException("Location Number is required but is missing in the OED file")

        uni_exposure['loc_id'] = str(loc['locnumber'])
        if loc["longitude"] > 0 or loc["latitude"] < 0:  # todo: check that lat/lon is indeed in AU or NZ
            uni_exposure['latitude'] = loc['latitude']
            uni_exposure['longitude'] = loc['longitude']
            uni_exposure['best_res'] = EnumResolution.LatLong.value
            if uni_exposure['med_id'] is None and self._postcode_lookup:
                uni_exposure['med_id'] = self._postcode_lookup.get_postcode(loc["longitude"], loc["latitude"])
                if uni_exposure['med_id'] is None and self._peril_id is not None \
                        and self._peril_id & OEDPeril.Hail.value > 0:
                    raise LocationLookupException("Cannot find postcode for location " + str(uni_exposure['loc_id']) +
                                                  ". Postcode is required for " + str(OEDPeril.Hail))
            if uni_exposure['lrg_id'] and self._postcode_lookup:
                pass  # todo: this is not required since we do not handle aggregation or display in oasis

        # todo: handle missing geolocation here (i.e. no address, no latlong, no cresta, no postcode
        # uni_exposure['address_id'] # todo: lookup for address id in user_defined_1
        # uni_exposure['address_type']

        uni_exposure['country_code'] = "au"

        # uni_exposure['state'] # this must be 3 chars

        # uni_exposure['zone_type']
        # uni_exposure['zone_id']

        # uni_exposure['catchment_type'] # todo: when implementing flood
        # uni_exposure['catchment_id']

        # uni_exposure['fine_type']
        # uni_exposure['fine_id']

        uni_exposure['props'] = {"YearBuilt": int(loc['yearbuilt']) if 'yearbuilt' in loc else 0}

        # uni_exposure['modelled']

        return uni_exposure

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
    loc = {'locnumber': 1, 'latitude': -33.8688, 'longitude': 151.2093}
    print(cl.process_location(loc, 1))
