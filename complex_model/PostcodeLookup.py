# -*- coding: utf-8 -*-

import csv, json
from shapely.geometry import shape, Point
from os import path
from complex_model.QuadTree import QuadTree


# from multiprocessing.pool import ThreadPool


class PostcodeLookup(object):
    """Functionality to perform postcode lookup"""

    _keys_file_dir = None

    _postcode_boundary_file = "postcode_boundaries.json"
    _postcode_boundaries = {}
    _postcode_grid_file = "postcode_grid.csv"
    _postcode_cellid_file = "cellid_to_postcode.csv"
    _postcode_quadtree = QuadTree(8, 8, -44.36151598, 115.35990092, 2.56)
    _cellid_to_postcode = {}

    def __init__(self, keys_file_dir=None):
        self._keys_file_dir = keys_file_dir
        if self._keys_file_dir:
            self._load_postcode_boundaries()

    def _load_postcode_boundaries(self):
        # loading cellid-postcode lookup first
        with open(path.join(self._keys_file_dir, self._postcode_cellid_file), 'r') as f:
            reader = csv.DictReader(f, delimiter=",")
            for row in reader:
                cellid = str(row["cellid"])
                postcode = int(row["postcode"])
                if cellid not in self._cellid_to_postcode:
                    self._cellid_to_postcode[cellid] = []
                self._cellid_to_postcode[cellid].append(postcode)

        # now we load the quad tree
        with open(path.join(self._keys_file_dir, self._postcode_grid_file), 'r') as f:
            reader = csv.DictReader(f, delimiter=",")
            for row in reader:
                cellid = str(row["cellid"])
                latitude = float(row["latitude"])
                longitude = float(row["longitude"])
                size = float(row["size"]) / 2
                self._postcode_quadtree.Load(cellid, latitude, longitude, size)

        # now we load the postcode boundary shapes
        with open(path.join(self._keys_file_dir, self._postcode_boundary_file), 'r') as f:
            boundaries_json = json.load(f)

        for feature in boundaries_json["features"]:
            postcode = feature["properties"]["postcode"]
            if postcode not in self._postcode_boundaries.keys():
                self._postcode_boundaries[postcode] = []
            self._postcode_boundaries[postcode].append(shape(feature["geometry"]))

    def get_postcode(self, lon, lat):
        """Get postcode of a given latitude and longitude

        :param lon: latitude of the point
        :param lat: longitude of the point
        :return: an integer representing the postcode
        """
        if lat is None or lon is None:
            return None
        point = Point(float(lon), float(lat))
        quad = self._postcode_quadtree.Lookup(lat, lon)
        if quad:
            postcodes = self._cellid_to_postcode[quad.CellID]
            for postcode in postcodes:
                if postcode in self._postcode_boundaries.keys():
                    for polygon in self._postcode_boundaries[postcode]:
                        if polygon.contains(point):
                            return postcode
        return None
