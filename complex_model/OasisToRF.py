import os
import json
from enum import Enum
import sqlite3
from shutil import copyfile

"""
This script is used to transform oasis item and coverage files into cannonical rf item and coverage files stored in a sqlite database
1. copy template database from the specified risk_platform_data folder
2. convert oasis items.csv and coverages.csv into u_item and u_coverage tables
"""

DEFAULT_DB = "riskfrontiersdbAUS_v2_4_1.db"

RF_DEFAULT_ITEM_SQLITE_DEF = {
    "loc_id": {"datatype": "INTEGER", "default": None},
    "latitude": {"datatype": "REAL", "default": None},
    "longitude": {"datatype": "REAL", "default": None},
    "address_type": {"datatype": "INTEGER", "default": None},
    "address_id": {"datatype": "INTEGER", "default": None},
    "best_res": {"datatype": "INTEGER", "default": None},
    "country_code": {"datatype": "TEXT", "default": None},
    "state": {"datatype": "TEXT", "default": None},
    "zone_type": {"datatype": "INTEGER", "default": None},
    "zone_id": {"datatype": "INTEGER", "default": None},
    "catchment_type": {"datatype": "INTEGER", "default": None},
    "catchment_id": {"datatype": "INTEGER", "default": None},
    "lrg_type": {"datatype": "INTEGER", "default": None},
    "lrg_id": {"datatype": "INTEGER", "default": None},
    "med_type": {"datatype": "INTEGER", "default": None},
    "med_id": {"datatype": "INTEGER", "default": None},
    "fine_type": {"datatype": "INTEGER", "default": None},
    "fine_id": {"datatype": "INTEGER", "default": None},
    "lob_id": {"datatype": "INTEGER", "default": None},
    "props": {"datatype": "TEXT", "default": None},
    "modelled": {"datatype": "INTEGER", "default": None},
    "origin_file_line": {"datatype": "INTEGER", "default": 0},
}

RF_DEFAULT_COVERAGE_SQLITE_DEF = {
    "loc_id": {"datatype": "INTEGER", "default": None},
    "cover_id": {"datatype": "INTEGER", "default": None},
    "peril_id": {"datatype": "INTEGER", "default": None},
    "value": {"datatype": "REAL", "default": None},
    "currency": {"datatype": "TEXT", "default": None},
    "deductible": {"datatype": "REAL", "default": None},
    "limit": {"datatype": "REAL", "default": None},
    "scale_id": {"datatype": "INTEGER", "default": None},
    "origin_file_line": {"datatype": "INTEGER", "default": 0}, }

RF_DEFAULT_ITEM = dict([(col, RF_DEFAULT_ITEM_SQLITE_DEF[col]["default"]) for col in RF_DEFAULT_ITEM_SQLITE_DEF])
RF_DEFAULT_COVERAGE = dict(
    [(col, RF_DEFAULT_COVERAGE_SQLITE_DEF[col]["default"]) for col in RF_DEFAULT_COVERAGE_SQLITE_DEF])


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


def get_connection_string(db_fp):
    return "Data Source=" + db_fp + ";Version=3;"


def create_rf_input(item_source, coverage_source, sqlite_fp, risk_platform_data):
    """This function populates Risk Frontiers exposure and coverage database from oasis generated input files.
    Precondition: The number of rows in item_source and coverage_source must be exactly the same.

    :param item_source: the items.csv as a dataframe.
    :param coverage_source: the coverages.csv as a dataframe
    :param sqlite_fp: path to store the sqlite database containing the exposure and coverage tables
    :param risk_platform_data: path containing the template databases for Risk Frontiers models
    :return: a number of rows in the items and coverages.

    """
    num_items = len(item_source)
    num_coverages = len(coverage_source)
    if not num_items == num_coverages:
        raise Exception("the items.csv and coverage.csv must have the exact same number of rows")

    if os.path.isfile(sqlite_fp):
        os.remove(sqlite_fp)
    copyfile(os.path.join(risk_platform_data, DEFAULT_DB), sqlite_fp)

    con = sqlite3.connect(sqlite_fp)
    cur = con.cursor()

    cur.execute("CREATE TABLE u_exposure (" + ",".join(
        ["[" + col + "] " + RF_DEFAULT_ITEM_SQLITE_DEF[col]["datatype"] for col in RF_DEFAULT_ITEM_SQLITE_DEF]) + ");")
    cur.execute("CREATE INDEX u_exposure_idx ON u_exposure (origin_file_line);")
    cur.execute("CREATE TABLE u_coverage (" + ",".join(
        ["[" + col + "] " + RF_DEFAULT_COVERAGE_SQLITE_DEF[col]["datatype"] for col in
         RF_DEFAULT_COVERAGE_SQLITE_DEF]) + ");")
    cur.execute("CREATE INDEX u_coverage_idx ON u_coverage (origin_file_line);")

    line_id = 0
    items = []
    coverages = []
    for line_id in range(0, num_items):
        item_row = item_source.iloc[line_id]
        coverage_row = coverage_source.iloc[line_id]
        # building item row
        rf_item = RF_DEFAULT_ITEM.copy()

        model_data = json.loads(item_row['model_data'])
        for key in rf_item.keys():
            if key in model_data and model_data[key]:
                if key.lower() == "props":
                    rf_item[key] = json.dumps(model_data[key])
                else:
                    rf_item[key] = model_data[key]

        if not rf_item['loc_id']:
            # rf_item['loc_id'] = "rf_loc_" + str(model_data['origin_file_line'])
            rf_item['loc_id'] = item_row['item_id']

        # building coverage row
        rf_coverage = RF_DEFAULT_COVERAGE.copy()

        rf_coverage['cover_id'] = int(model_data['cover_id'])
        rf_coverage['value'] = float(coverage_row['tiv'])

        rf_coverage['loc_id'] = rf_item['loc_id']

        # for oasis origin_file_line will be item_id/coverage_id
        rf_item['origin_file_line'] = line_id + 1
        rf_coverage['origin_file_line'] = rf_item['origin_file_line']

        items.append(tuple(rf_item.values()))
        coverages.append(tuple(rf_coverage.values()))

    item_sql = "INSERT INTO u_exposure VALUES (" + ",".join(["?" for c in RF_DEFAULT_ITEM]) + ");";
    coverage_sql = "INSERT INTO u_coverage VALUES (" + ",".join(["?" for c in RF_DEFAULT_COVERAGE]) + ");";
    cur.executemany(item_sql, items)
    cur.executemany(coverage_sql, coverages)
    con.commit()
    con.close()
    return line_id
