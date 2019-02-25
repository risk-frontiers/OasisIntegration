import itertools
from interface import implements
import json

import oasislmf.utils.peril
import oasislmf.utils.coverage
from oasislmf.utils.metadata import (
    OASIS_KEYS_SC,
    OASIS_KEYS_FL,
    OASIS_KEYS_NM,
    OASIS_KEYS_STATUS)
from oasislmf.model_preparation.lookup import OasisBaseKeysLookup

class DummyComplexModelKeysLookup(OasisBaseKeysLookup):

    def __init__(self, 
            keys_data_directory=None,
            supplier=None,
            model_name=None,
            model_version=None):

        self._peril_ids = [
            oasislmf.utils.peril.PERIL_ID_WIND,
            oasislmf.utils.peril.PERIL_ID_SURGE
        ]

        self._coverage_types = [
            oasislmf.utils.coverage.BUILDING_COVERAGE_CODE,
            oasislmf.utils.coverage.CONTENTS_COVERAGE_CODE
        ]


    def process_location(self, loc, peril_id, coverage_type):

        status = OASIS_KEYS_SC
        message = "OK"

        if (
            peril_id == oasislmf.utils.peril.PERIL_ID_WIND and
            coverage_type == oasislmf.utils.coverage.BUILDING_COVERAGE_CODE
        ):
            data = {
                "area_peril_id": 1,
                "vulnerability_id": 1
            }

        elif (
            peril_id == oasislmf.utils.peril.PERIL_ID_WIND and
            coverage_type == oasislmf.utils.coverage.CONTENTS_COVERAGE_CODE
        ):
            data = {
                "area_peril_id": 2,
                "vulnerability_id": 2
            }

        elif (
            peril_id == oasislmf.utils.peril.PERIL_ID_SURGE and
            coverage_type == oasislmf.utils.coverage.BUILDING_COVERAGE_CODE
        ):
            data = {
                "area_peril_id": 3,
                "vulnerability_id": 3
            }

        elif (
            peril_id == oasislmf.utils.peril.PERIL_ID_SURGE and
            coverage_type == oasislmf.utils.coverage.CONTENTS_COVERAGE_CODE
            ):
            data = {
                "area_peril_id": 4,
                "vulnerability_id": 4
            }

        return {
            'locnumber': loc['locnumber'],
            'peril_id': peril_id,
            'coverage_type': coverage_type,
            'model_data': json.dumps(data),
            'status': status,
            'message': message
        }

    def process_locations(self, locs):

        locs_seq = (loc for _, loc in locs.iterrows())
        for loc, peril_id, coverage_type in \
                itertools.product(locs_seq, self._peril_ids, self._coverage_types):
            yield self.process_location(loc, peril_id, coverage_type)
