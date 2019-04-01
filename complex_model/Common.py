# encoding: utf-8

""""This file contains constants translated from the MultiPeril Workbench and OED specification"""

from enum import Enum
from RFException import ArgumentOutOfRangeException


class OEDPeril(Enum):
    QuakeShake = 1
    FireFollowing = 2
    Tsunami = 4
    SprinklerLeakage = 8
    Landslide = 16
    Liquefaction = 32
    TropicalCyclone = 64
    ExtraTropicalCyclone = 128
    StormSurge = 256
    FluvialFlood = 512
    FlashSurfacePluvialFlood = 1024
    OtherConvectiveWind = 2048
    Tornado = 4096
    Hail = 8192
    Snow = 16384
    Ice = 32768
    Freeze = 65536
    NonCat = 131072
    Bushfire = 262144
    NBCRTerrorism = 524288
    ConventionalTerrorism = 1048576
    Lightning = 2097152
    WinterstormWind = 4194304
    Smoke = 8388608


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


def oed_to_rf_peril(oedPerilID):
    if oedPerilID == 8192:
        return EnumPeril.Hail
    if oedPerilID == 1:
        return EnumPeril.Quake
    if oedPerilID == 512:
        return EnumPeril.RiverineFlood
    if oedPerilID == 262144:
        return EnumPeril.Bushfire
    if oedPerilID == 64:
        return EnumPeril.Cyclone


PerilSet = {
    "hailaus": {"OED_ID": 8192, "COUNTRY": "au", "MAX_EVENT_INDEX": 134704731},
    "quakeaus": {"OED_ID": 1, "COUNTRY": "au", "MAX_EVENT_INDEX": 1000252},
    "floodaus": {"OED_ID": 512, "COUNTRY": "au", "MAX_EVENT_INDEX": 535000},
    "fireaus": {"OED_ID": 262144, "COUNTRY": "au", "MAX_EVENT_INDEX": 291577},
    "cyclaus": {"OED_ID": 64, "COUNTRY": "au", "MAX_EVENT_INDEX": 371653},
    "quakenz": {"OED_ID": 1, "COUNTRY": "nz", "MAX_EVENT_INDEX": 10441016},
}
PerilSet = {x: {"OED_ID": PerilSet[x]["OED_ID"],
                "COUNTRY": PerilSet[x]["COUNTRY"],
                "RF_ID": oed_to_rf_peril(PerilSet[x]["OED_ID"])}
            for x in PerilSet}


RFPerilMask = OEDPeril.Bushfire.value | OEDPeril.QuakeShake.value | OEDPeril.FluvialFlood.value |\
              OEDPeril.TropicalCyclone.value | OEDPeril.Hail.value


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
