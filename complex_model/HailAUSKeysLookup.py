import itertools
import json
import numbers
import math
import sqlite3
import os
from datetime import date

from oasislmf.utils.coverages import COVERAGE_TYPES
from oasislmf.utils.status import OASIS_KEYS_STATUS
from oasislmf.preparation.lookup import OasisBaseKeysLookup

from complex_model.PostcodeLookup import PostcodeLookup
from complex_model.PostcodeDictionary import POSTCODE_CONCORDANCE, POSTCODE_SET, DELIVERY_POSTCODE_SET
from complex_model.RFException import LocationLookupException, LocationNotModelledException
from complex_model.Common import *
from complex_model.DefaultSettings import COUNTRY_CODE, BASE_DB_NAME
from complex_model.utils import is_integer, to_bool, is_float, is_number


class HailAUSKeysLookup(OasisBaseKeysLookup):
    def __init__(self,
                 keys_data_directory=None,
                 supplier=None,
                 model_name=None,
                 model_version=None,
                 complex_lookup_config_fp=None,
                 output_directory=None):
        self.keys_file_dir = keys_data_directory
        self._coverage_types = [
            COVERAGE_TYPES['buildings']['id'],  # 1, building/motor
            COVERAGE_TYPES['contents']['id'],  # 3, contents
            COVERAGE_TYPES['bi']['id'],  # 4, bi
            COVERAGE_TYPES['other']['id']  # 2, other]
        ]
        self._supported_coverage_types = [
            COVERAGE_TYPES['buildings']['id'],  # 1, building/motor
            COVERAGE_TYPES['contents']['id'],  # 3, contents
            COVERAGE_TYPES['bi']['id'],  # 4, bi
        ]
        self._peril_id = None
        if model_name is not None and model_name.lower() in PerilSet.keys():
            self._peril_id = PerilSet[model_name.lower()]['OED_ID']
        self._postcode_lookup = None
        self._supported_gnaf = []
        if self.keys_file_dir:
            self._postcode_lookup = PostcodeLookup(keys_file_dir=self.keys_file_dir)
            db = sqlite3.connect(os.path.abspath(
                os.path.join(self.keys_file_dir, '..', BASE_DB_NAME)))
            cur = db.cursor()
            cur.execute("select address_id from rf_address;")
            res = cur.fetchall()
            db.close()
            self._supported_gnaf = set([x[0] for x in res])
        self._codes_mapping = {"construction": {"column": "constructioncode", "code": OED_CONSTRUCTION_CODE},
                               "occupancy": {"column": "occupancycode", "code": OED_OCCUPANCY_CODE}}

    def _get_lob_id(self, record):
        """This transforms the occupancy error_code into Multi-Peril Workbench specified line of business"""
        try:
            if 'occupancycode' not in record:
                # residential: this is the default behaviour when this field is missing in the workbench
                return EnumLineOfBusiness.Residential.value
            if self._check_in_group(record, "residential",  self._codes_mapping["occupancy"]):
                return EnumLineOfBusiness.Residential.value  # residential
            elif self._check_in_group(record, "commercial",  self._codes_mapping["occupancy"]):
                return EnumLineOfBusiness.Commercial.value  # commercial
            elif self._check_in_group(record, "industrial",  self._codes_mapping["occupancy"]):
                return EnumLineOfBusiness.Industrial.value  # industrial
            else:
                raise LocationNotModelledException("Unsupported occupancy code " + str(record['occupancycode']),
                                                   error_code=230)
        except TypeError:
            raise LocationLookupException("Badly formatted occupancy code " + str(record['occupancycode']),
                                          error_code=123)

    def _check_in_group(self, record, group: str, codes_mapping: dict):
        cc = record[codes_mapping["column"]]
        for bound in codes_mapping["code"][group]:
            if bound['min'] <= cc <= bound['max']:
                return True
        return False

    def _is_motor(self, record):
        try:
            return self._check_in_group(record, "motor", self._codes_mapping["construction"])
        except KeyError or TypeError:
            return False

    def _is_unsupported_construction_code(self, record):
        try:
            return self._check_in_group(record, "unsupported", self._codes_mapping["construction"])
        except KeyError or TypeError:
            return False

    def _is_unsupported_occupancy_code(self, record):
        try:
            return self._check_in_group(record, "unsupported", self._codes_mapping["occupancy"])
        except KeyError or TypeError:
            return False

    def _pre_validate(self, record, coverage_type: int):
        """This validates the record forwarded by the oasislmf framework is supported

        :param record:
        :return: raises an exception if record is not supported
        """
        # OED: locperilscovered is required
        if 'locperilscovered' not in record or record['locperilscovered'] is None:
            raise LocationLookupException('LocPerilsCovered is required', error_code=101)
        loc_peril_covered_ids = get_covered_ids(record['locperilscovered'])
        if self._peril_id not in loc_peril_covered_ids:
            raise LocationLookupException('Location not covered for ' + str(oed_to_rf_peril(self._peril_id)),
                                          error_code=122)

        # OASIS: loc_id is uniquely generated for each location by oasis
        if 'loc_id' not in record or record['loc_id'] is None:
            raise LocationLookupException("Location ID is required but is missing",
                                          error_code=102)

        # Unsupported coverage (Other TIV is not supported)
        if coverage_type == COVERAGE_TYPES['other']['id']:  # Other TIV is not supported anymore
            if float(record["othertiv"]) > 0:
                raise LocationNotModelledException("Other coverage is not modelled. MotorTIV is parsed from BuildingTIV",
                                                   error_code=210)

        # Unsupported occupancy code

        # Unsupported construction code
        if coverage_type in self._supported_coverage_types and self._is_unsupported_construction_code(record):
            raise LocationNotModelledException("Unsupported construction code", error_code=230)

    def _post_validate(self, uni_exposure: dict, record):
        """This validates the uni_exposure as per the Multi-Peril Workbench specification
                1. we ignore a location that has no postcode if the peril is Hail
                2. we ignore location that has not geographical specification (address, lat/lon, cresta, ica_zone)

        :param uni_exposure:
        :return: validated uni_exposure
        """
        # incomplete or missing geo-location field should fail
        if not (
                (uni_exposure['latitude'] and uni_exposure['longitude']) or
                self.is_valid_address(uni_exposure['address_id'], uni_exposure['address_type']) or
                uni_exposure['med_id'] or
                uni_exposure['zone_id'] or
                uni_exposure['lrg_id']
        ):
            raise LocationLookupException("A location must have at least a valid Cresta, Ica Zone, Postalcode, Lat/Lon "
                                          "or address id (GNAF ID)", error_code=110)

        # Residential with BI coverage should fail
        if (uni_exposure['lob_id'] == EnumLineOfBusiness.Residential.value and
                uni_exposure['cover_id'] == EnumCover.BI.value):
            raise LocationLookupException("Business Interruption losses are not currently modelled for Residential "
                                          "line of business", error_code=151)

        # Motor construction code but cover is not Motor should fail
        if self._is_motor(record) and uni_exposure['cover_id'] in (EnumCover.Building.value, EnumCover.Contents.value,
                                                                   EnumCover.BI.value):
            raise LocationLookupException("If row has a motor construction code (between 5850 and 5950) then it cannot "
                                          "have cover other than Motor (TIV stored in OtherTIV)", error_code=210)

        return uni_exposure

    def _add_geog_name(self, uni_exposure: dict, geog_scheme: str, geog_name: str):
        """This parses custom geo-location: GNAF ID, Cresta and ICAZone

        :param uni_exposure:
        :param geog_scheme: valid RF supported geography scheme
        :param geog_name: valid RF supported region value
        :return: the uni exposure object where the respective geo-location has been set
        """
        # GNAF address
        if geog_scheme == "GNAF" and type(geog_name) == str and not geog_name == "":
            uni_exposure["address_id"] = geog_name
            uni_exposure['address_type'] = EnumAddressType.GNAF.value

        # ica zone
        if geog_scheme == "ICA" and is_integer(geog_name) and 0 < int(geog_name) < 50:
            uni_exposure["lrg_id"] = int(geog_name)
            uni_exposure['lrg_type'] = EnumResolution.IcaZone.value

        # cresta
        if geog_scheme == "CRO" and is_integer(geog_name) and 0 < int(geog_name) < 50:
            uni_exposure["zone_id"] = int(geog_name)
            uni_exposure['zone_type'] = EnumResolution.Cresta.value

        # postcode
        if geog_scheme == "PC4" and is_integer(geog_name) and 0 < int(geog_name):
            uni_exposure['med_id'] = int(geog_name)
            uni_exposure['med_type'] = EnumResolution.Postcode.value

        return uni_exposure

    def create_uni_exposure(self, record, coverage_type: int):
        """This creates a uni_exposure object from an oasis loc object.
        The u_exposure table contains the following columns:

        loc_id, latitude, longitude, address_type, address_id, best_res, country_code, state, zone_type, zone_id,
        catchment_type, catchment_id, lrg_type, lrg_id, med_type, med_id, fine_type, fine_id, lob_id, props, modelled,
        origin_file_line

        :param record: a row from a OED portfolio
        :param coverage_type: is a either building [1], contents [3], other [3] (motor) or business interruption [4]
        :return: a uni_exposure object as per the Multi-Peril Workbench specification
        """

        self._pre_validate(record, coverage_type)

        uni_exposure = dict()
        uni_exposure['loc_id'] = str(record['loc_id'])
        uni_exposure['lob_id'] = self._get_lob_id(record)
        uni_exposure['cover_id'] = oed_to_rf_coverage(coverage_type, self._is_motor(record))

        # OED: country error_code is also required but we'll default to AU if missing
        try:
            uni_exposure['country_code'] = str(record["countrycode"]).lower()
        except (ValueError, KeyError):
            uni_exposure['country_code'] = COUNTRY_CODE

        # address, ICA zone and cresta
        uni_exposure['address_id'] = None
        uni_exposure['address_type'] = None
        uni_exposure['med_id'] = None
        uni_exposure['med_type'] = None
        uni_exposure['lrg_id'] = None
        uni_exposure['lrg_type'] = None
        uni_exposure['zone_id'] = None
        uni_exposure['zone_type'] = None
        for i in range(1, 6):
            geog_scheme_col = "geogscheme" + str(i)
            geog_name_col = "geogname" + str(i)
            try:
                if geog_scheme_col in record and geog_name_col in record:
                    uni_exposure = self._add_geog_name(uni_exposure, record[geog_scheme_col], record[geog_name_col])
            except (ValueError, TypeError):
                pass

        # overwrite postcode from 'postalcode' field
        if 'postalcode' in record and self.is_valid_postcode(record['postalcode']):
            postcode = int(record['postalcode'])
            if postcode in DELIVERY_POSTCODE_SET:
                postcode = POSTCODE_CONCORDANCE[str(postcode)]
            uni_exposure['med_id'] = postcode
            uni_exposure['med_type'] = EnumResolution.Postcode.value

        # lat/lon
        uni_exposure['latitude'] = None
        uni_exposure['longitude'] = None
        if 'longitude' in record and is_float(record['longitude']) \
                and 'latitude' in record and is_float(record['latitude']) \
                and not record['longitude'] == 0 and not record['latitude'] == 0 \
                and not math.isnan(record['longitude']) and not math.isnan(record['latitude']):
            if AU_BOUNDING_BOX['MIN'][0] <= record["longitude"] <= AU_BOUNDING_BOX['MAX'][0] \
                    and AU_BOUNDING_BOX['MIN'][1] <= record["latitude"] <= AU_BOUNDING_BOX['MAX'][1]:
                uni_exposure['latitude'] = record['latitude']
                uni_exposure['longitude'] = record['longitude']
                if (uni_exposure['med_id'] is None or uni_exposure['med_id'] == 0) and self._postcode_lookup:
                    uni_exposure['med_id'] = self._postcode_lookup.get_postcode(record["longitude"], record["latitude"])
                if uni_exposure['lrg_id'] is None or uni_exposure['lrg_id'] == 0:
                    pass  # not required at lat/lon level
            else:
                raise LocationLookupException("Location is not in Australia", error_code=121)

        # setting best res
        if uni_exposure['lrg_id'] is not None and uni_exposure['lrg_id'] > 0:
            uni_exposure['best_res'] = EnumResolution.IcaZone.value
        if uni_exposure['zone_id'] is not None and uni_exposure['zone_id'] > 0:
            uni_exposure['best_res'] = EnumResolution.Cresta.value
        if uni_exposure['med_id'] is not None and uni_exposure['med_id'] > 0:
            uni_exposure['best_res'] = EnumResolution.Postcode.value
        if uni_exposure['address_id'] is not None and \
                self.is_valid_address(uni_exposure['address_id'], uni_exposure['address_type']):
            uni_exposure['best_res'] = EnumResolution.Address.value
        if uni_exposure['latitude'] is not None and uni_exposure['longitude'] is not None:
            uni_exposure['best_res'] = EnumResolution.LatLong.value

        uni_exposure['state'] = None
        if 'areacode' in record and str(record["areacode"]).upper() in AU_STATES:
            uni_exposure['state'] = str(record["areacode"]).upper()

        # uni_exposure['catchment_type'] # todo: when implementing flood
        # uni_exposure['catchment_id']

        # uni_exposure['fine_type']
        # uni_exposure['fine_id']

        # uni_exposure["props"]
        props = {}
        try:
            props["YearBuilt"] = self.sanitize_year_built(int(record['yearbuilt']))
        except (ValueError, TypeError, KeyError):
            pass

        try:
            props['StaticMotor'] = self.sanitize_smv(record, to_bool(record['staticmotorvehicle']))
        except (ValueError, TypeError, KeyError):
            pass

        uni_exposure['props'] = props
        # uni_exposure['modelled'] # todo: when implementing flood, check that location is in flood zone

        return self._post_validate(uni_exposure, record)

    def sanitize_year_built(self, year: int):
        if 0 < year <= date.today().year + 1:
            return year
        return 0

    def sanitize_smv(self, record, smv):
        try:
            if self._check_in_group(record, "motor_marine", self._codes_mapping["construction"]):
                return True
            return smv
        except KeyError or TypeError:
            return smv

    def is_valid_address(self, address_id: str, address_type: EnumAddressType):
        if not address_type == EnumAddressType.GNAF.value:
            return False
        return address_id in self._supported_gnaf

    def is_valid_postcode(self, postcode):
        if not is_integer(postcode):
            return False
        postcode = int(postcode)
        if postcode in POSTCODE_SET or postcode in DELIVERY_POSTCODE_SET:
            return True
        return False

    def __skip_coverage(self, loc, coverage_type: int):
        # skip (loc, coverage) if TIV is 0
        if coverage_type == COVERAGE_TYPES['buildings']['id'] and \
                is_float(loc["buildingtiv"]) and \
                float(loc["buildingtiv"]) > 0:  # buildings and motor
            return False
        if coverage_type == COVERAGE_TYPES['contents']['id'] and \
                is_float(loc["contentstiv"]) and \
                float(loc["contentstiv"]) > 0:  # contents
            return False
        if coverage_type == COVERAGE_TYPES['bi']['id'] and \
                is_float(loc["bitiv"]) and \
                float(loc["bitiv"]) > 0:  # bi
            return False
        if coverage_type == COVERAGE_TYPES['other']['id'] and \
                is_float(loc["othertiv"]) and \
                float(loc["othertiv"]) > 0:  # unsupported
            raise LocationNotModelledException("Other coverage is not supported", error_code=210)
        return True

    def process_location(self, record, coverage_type: int):
        try:
            if self.__skip_coverage(record, coverage_type):
                return None
            uni_exposure = self.create_uni_exposure(record, coverage_type)
            return {
                'loc_id': record['loc_id'],
                'peril_id': self._peril_id,
                'coverage_type': coverage_type,
                'model_data': json.dumps(uni_exposure),
                'status': OASIS_KEYS_STATUS['success']['id'],
                'message': "OK"
            }
        except LocationLookupException as e:
            return {
                'loc_id': record['loc_id'],
                'peril_id': self._peril_id,
                'coverage_type': coverage_type,
                'status': OASIS_KEYS_STATUS['fail']['id'],
                'message': str(e)
            }
        except LocationNotModelledException as e:
            return {
                'loc_id': record['loc_id'],
                'peril_id': self._peril_id,
                'coverage_type': coverage_type,
                'status': OASIS_KEYS_STATUS['nomatch']['id'],
                'message': str(e)
            }

    def process_locations(self, locs):
        locs_seq = (record for _, record in locs.iterrows())
        for loc, coverage_type in itertools.product(locs_seq, self._coverage_types):
            ret = self.process_location(loc, coverage_type)
            if ret is not None:
                yield ret
