

from enum import Enum


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


PerilSet = {
    "hailaus": {"OED_ID": 8192, "RF_ID": EnumPeril.Hail, "COUNTRY": "au"},
    "quakeaus": {"OED_ID": 1, "RF_ID": EnumPeril.Quake, "COUNTRY": "au"},
    "floodaus": {"OED_ID": 512, "RF_ID": EnumPeril.RiverineFlood, "COUNTRY": "au"},
    "fireaus": {"OED_ID": 262144, "RF_ID": EnumPeril.Bushfire, "COUNTRY": "au"},
    "cyclaus": {"OED_ID": 64, "RF_ID": EnumPeril.Cyclone, "COUNTRY": "au"},
    "quakenz": {"OED_ID": 1, "RF_ID": EnumPeril.Quake, "COUNTRY": "nz"},
}