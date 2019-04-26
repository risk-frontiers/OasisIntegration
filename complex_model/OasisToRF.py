import os
import json
import sqlite3
from shutil import copyfile
from complex_model.Common import EnumResolution

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


def get_connection_string(db_fp):
    return "Data Source=" + db_fp + ";Version=3;"


def is_valid_model_data(risk_platform_data):
    return os.path.isfile(os.path.join(risk_platform_data, DEFAULT_DB))


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

    cur.execute("CREATE TABLE u_exposure_tmp (" + ",".join(
        ["[" + col + "] " + RF_DEFAULT_ITEM_SQLITE_DEF[col]["datatype"] for col in RF_DEFAULT_ITEM_SQLITE_DEF]) + ");")
    cur.execute("CREATE TABLE u_exposure (" + ",".join(
        ["[" + col + "] " + RF_DEFAULT_ITEM_SQLITE_DEF[col]["datatype"] for col in RF_DEFAULT_ITEM_SQLITE_DEF]) + ");")
    cur.execute("CREATE TABLE u_coverage (" + ",".join(
        ["[" + col + "] " + RF_DEFAULT_COVERAGE_SQLITE_DEF[col]["datatype"] for col in
         RF_DEFAULT_COVERAGE_SQLITE_DEF]) + ");")

    origin_file_line = 0
    items = []
    coverages = []
    for line_id in range(0, num_items):
        item_row = item_source.iloc[line_id]
        coverage_row = coverage_source.iloc[line_id]
        origin_file_line = line_id + 1
        # building item row
        rf_item = RF_DEFAULT_ITEM.copy()

        model_data = json.loads(item_row['model_data'])
        for key in rf_item.keys():
            if key in model_data and model_data[key] is not None:
                if key.lower() == "props":
                    rf_item[key] = json.dumps(model_data[key])
                else:
                    rf_item[key] = model_data[key]

        # if not rf_item['loc_id']:
            # rf_item['loc_id'] = "rf_loc_" + str(model_data['loc_id'])
        rf_item['loc_id'] = str(item_row['item_id'])

        # building coverage row
        rf_coverage = RF_DEFAULT_COVERAGE.copy()

        rf_coverage['cover_id'] = int(model_data['cover_id'])
        rf_coverage['value'] = float(coverage_row['tiv'])

        rf_coverage['loc_id'] = rf_item['loc_id']

        # for oasis origin_file_line will be item_id/coverage_id
        rf_item['origin_file_line'] = origin_file_line
        rf_coverage['origin_file_line'] = origin_file_line

        items.append(tuple(rf_item.values()))
        coverages.append(tuple(rf_coverage.values()))

    item_sql = "INSERT INTO u_exposure_tmp VALUES (" + ",".join(["?" for c in RF_DEFAULT_ITEM]) + ");"
    coverage_sql = "INSERT INTO u_coverage VALUES (" + ",".join(["?" for c in RF_DEFAULT_COVERAGE]) + ");"
    cur.executemany(item_sql, items)
    cur.executemany(coverage_sql, coverages)
    con.commit()

    # spatial analysis ...
    fill_resolution_from_address_id(con, cur)
    fill_resolution_from_lat_long(con, cur)

    # post processing
    delete_temp_exposure = "DROP TABLE u_exposure_tmp;"
    ofl_exposure_index = "CREATE INDEX ofl_exposure_index ON u_exposure (origin_file_line);"
    ofl_coverage_index = "CREATE INDEX ofl_coverage_index ON u_coverage (origin_file_line);"
    cur.execute(delete_temp_exposure)
    cur.execute(ofl_exposure_index)
    cur.execute(ofl_coverage_index)
    con.commit()

    con.close()
    return origin_file_line


ADDRESS_COLUMN_AUTOPOPULATE = [EnumResolution.Latitude, EnumResolution.Longitude, EnumResolution.Postcode,
                               EnumResolution.Cresta, EnumResolution.State]


def fill_resolution_from_address_id(con, cur):
    """This function populate rows with valid GNAF IDs (not lat/lon)

    :param con: sqlite connection to the database containing the exposure table
    :param cur: sqlite cursor
    """
    address_fill_sql = """INSERT INTO u_exposure
                SELECT a.loc_id, 
                CASE WHEN a.latitude IS NULL OR a.latitude = 0 THEN b.latitude ELSE a.latitude END latitude,
                CASE WHEN a.longitude IS NULL OR a.longitude = 0 THEN b.longitude ELSE a.longitude END longitude,
                a.address_type,
                a.address_id,
                a.best_res,
                a.country_code,
                CASE WHEN a.[state] IS NULL THEN b.[state] ELSE a.[state] END [state],
                2 zone_type,
                CASE WHEN a.zone_id IS NULL THEN b.cresta ELSE a.zone_id END zone_id,		
                4 catchment_type,
                CASE WHEN a.catchment_id IS NULL THEN b.catchment_id ELSE a.catchment_id END catchment_id,
                3 lrg_type,
                CASE WHEN a.lrg_id IS NULL THEN b.ica_zone ELSE a.lrg_id END lrg_id,
                1 med_type,
                CASE WHEN a.med_id IS NULL OR a.med_id = 0 THEN b.postcode ELSE a.med_id END med_id,
                a.fine_type,
                a.fine_id,
                a.lob_id,
                a.props,
                a.modelled,
                a.origin_file_line
        FROM u_exposure_tmp a INNER JOIN rf_address b ON a.address_id = b.address_id 
        WHERE NOT a.address_id IS NULL AND country_code = "au" AND 
            (a.latitude = 0 OR a.latitude IS NULL OR a.longitude = 0 or a.longitude IS NULL)
        UNION ALL SELECT * FROM u_exposure_tmp WHERE NOT (NOT address_id IS NULL AND country_code = "au" AND 
            (latitude = 0 OR latitude IS NULL OR longitude = 0 or longitude IS NULL));"""
    lookup_cond = """NOT a.address_id IS NULL AND country_code = "au" AND (a.latitude = 0 OR a.longitude = 0)"""
    address_fill_sql = address_fill_sql.format(lookup_cond)
    cur.execute(address_fill_sql)
    con.commit()


def fill_resolution_from_lat_long(con, cur):
    pass  # todo: required when implementing flood to get catchment id etc
