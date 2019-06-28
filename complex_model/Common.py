# encoding: utf-8

""""This file contains constants translated from the MultiPeril Workbench and OED specification"""

from enum import Enum
from oasislmf.utils.peril import PERILS, PERIL_GROUPS
from complex_model.RFException import ArgumentOutOfRangeException

class EnumPeril(Enum):
    Structure = -3
    MultiPeril = -2
    Undefined = -1
    RiverineFlood = 0
    Bushfire = 1
    Hail = 2
    Quake = 3
    Cyclone = 4
    Volcano = 5


def oed_to_rf_peril(oed_peril_id):
    if oed_peril_id == 8192:
        return EnumPeril.Hail
    if oed_peril_id == 1:
        return EnumPeril.Quake
    if oed_peril_id == 512:
        return EnumPeril.RiverineFlood
    if oed_peril_id == 262144:
        return EnumPeril.Bushfire
    if oed_peril_id == 64:
        return EnumPeril.Cyclone


PerilSet = {
    "hailaus": {"OED_CODE": 8192, "OED_ID": "XHL", "COUNTRY": "au", "MAX_EVENT_INDEX": 134704731},
    "quakeaus": {"OED_CODE": 1, "OED_ID": "QEQ", "COUNTRY": "au", "MAX_EVENT_INDEX": 1000252},
    "floodaus": {"OED_CODE": 512, "OED_ID": "ORF", "COUNTRY": "au", "MAX_EVENT_INDEX": 535000},
    "fireaus": {"OED_CODE": 262144, "OED_ID": "BBF", "COUNTRY": "au", "MAX_EVENT_INDEX": 291577},
    "cyclaus": {"OED_CODE": 64, "OED_ID": "WTC", "COUNTRY": "au", "MAX_EVENT_INDEX": 371653},
    "quakenz": {"OED_CODE": 1, "OED_ID": "QEQ", "COUNTRY": "nz", "MAX_EVENT_INDEX": 10441016},
}
PerilSet = {x: {"OED_ID": PerilSet[x]["OED_ID"],
                "COUNTRY": PerilSet[x]["COUNTRY"],
                "RF_ID": oed_to_rf_peril(PerilSet[x]["OED_ID"]),
                "MAX_EVENT_INDEX": PerilSet[x]["MAX_EVENT_INDEX"]}
            for x in PerilSet}


def get_covered_ids(peril_id):
    res = [PERILS[x]['id'] for x in PERILS if PERILS[x]['id'] == peril_id]
    res = res + [peril for x in PERIL_GROUPS if PERIL_GROUPS[x]['id'] == peril_id
                 for peril in PERIL_GROUPS[x]['peril_ids']]
    return res


class EnumResolution(Enum):
    Undefined = 255
    LocId = 254
    All = 253
    Address = 0
    Postcode = 1
    Cresta = 2
    IcaZone = 3
    Catchment = 4
    State = 5
    Ccd = 6
    LatLong = 7
    Latitude = 8
    Longitude = 9
    Code = 10
    Todofuken = 11
    Shikuchoson = 12
    VolcanoGrid = 13
    Country = 14
    BeeHive = 15


AU_BOUNDING_BOX = {
    'MIN': (112.0000000, -44.0000000),
    'MAX': (154.0000000, -10.0000000)
}


def to_uni_scale_id(res):
    if res == EnumResolution.Address:
        return "address_id"
    if res == EnumResolution.Latitude:
        return "latitude"
    if res == EnumResolution.Longitude:
        return "longitude"
    if res == EnumResolution.Cresta:
        return "zone_id"
    if res == EnumResolution.IcaZone:
        return "lrg_id"
    if res == EnumResolution.Postcode:
        return "med_id"
    if res == EnumResolution.State:
        return "state"
    if res == EnumResolution.Ccd:
        return "fine_id"
    if res == EnumResolution.BeeHive:
        return "lrg_id"
    if res == EnumResolution.Catchment:
        return "catchment_id"
    if res == EnumResolution.Code or res == EnumResolution.Shikuchoson or res == EnumResolution.Todofuken:
        return "code"  # todo: this is wrong
    raise ArgumentOutOfRangeException("Unknown resolution " + str(res))


def to_uni_scale_type(res):
    if res == EnumResolution.State or res == EnumResolution.Latitude or res == EnumResolution.Longitude:
        return None
    if res == EnumResolution.Cresta:
        return "zone_type"
    if res == EnumResolution.IcaZone or res == EnumResolution.BeeHive:
        return "lrg_type"
    if res == EnumResolution.Postcode:
        return "med_type"
    if res == EnumResolution.Ccd:
        return "fine_type"
    if res == EnumResolution.Catchment:
        return "catchment_type"
    if res == EnumResolution.Code or res == EnumResolution.Shikuchoson or res == EnumResolution.Todofuken:
        return "code"  # todo: wrong
    # raise ArgumentOutOfRangeException("Unknown resolution " + str(res))
    return None


def to_db_column_name(res):
    if res == EnumResolution.LocId:
        return "loc_id"
    if res == EnumResolution.Latitude:
        return "latitude"
    if res == EnumResolution.Longitude:
        return "longitude"
    if res == EnumResolution.Cresta:
        return "cresta"
    if res == EnumResolution.IcaZone:
        return "ica_zone"
    if res == EnumResolution.Postcode:
        return "postcode"
    if res == EnumResolution.Address:
        return "address_id"
    if res == EnumResolution.Catchment:
        return "catchment_id"
    if res == EnumResolution.State:
        return "state"
    if res == EnumResolution.Ccd:
        return "ccd"
    if res == EnumResolution.BeeHive:
        return "beehive_50km"
    if res == EnumResolution.Code or res == EnumResolution.Shikuchoson or res == EnumResolution.Todofuken:
        return "code"
    raise ArgumentOutOfRangeException("Unknown resolution " + str(res))


def oed_to_rf_coverage(oed_cover):
    if oed_cover == 1:
        return 1  # Building
    if oed_cover == 2:
        return 4  # Motor
    if oed_cover == 3:
        return 2  # Contents
    if oed_cover == 4:
        return 3  # Business Interruption
