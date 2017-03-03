from qgis.core import *
from GlobalMapTiles import GlobalMercator

import sqlite3
import sys
import os
import site
import importlib
import gzip
import uuid
import json
import glob

class VtReader:
    _geo_type_options = {1: "Point", 2: "LineString", 3: "Polygon"}
    _json_data = {"Point": {}, "LineString": {}, "Polygon": {}}
    _extent = 4096    
    directory = os.path.abspath(os.path.dirname(__file__))
    temp_dir = "%s/tmp" % directory
    filePath = "%s/sample data/zurich_switzerland.mbtiles" % directory

    def __init__(self, iface):
        self.iface = iface
        self.import_libs()
        self._counter = 0
        self._bool = True
        self._mbtile_id = "name"

    def clear_temp_dir(self):
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        files = glob.glob("%s/*" % self.temp_dir)
        for f in files:
            os.remove(f)

    def import_libs(self):        
        site.addsitedir(os.path.join(self.temp_dir, '/ext-libs'))
        print "import google.protobuf"
        import google.protobuf
        print "importing google.protobuf succeeded"
        print "import mapbox_vector_tile"
        self.mvt = importlib.import_module("mapbox_vector_tile")
        print "importing mapbox_vector_tile succeeded"

    def do_work(self):
        self.clear_temp_dir()
        self._create_layer()
        self.connect_to_db() 
        row = self.get_data_from_db()
        self.handle_single_record(row)

    def connect_to_db(self):
        try:
            self.conn = sqlite3.connect(self.filePath)
            print "Successfully connected to db"
        except:
            print "Db connection failed:", sys.exc_info()
            return        

    def get_data_from_db(self):
        print "Reading data from db"
        zoom_level = 14
        sql_command = "SELECT * FROM tiles WHERE zoom_level = {} LIMIT 1;".format(zoom_level)
        try:
            cur = self.conn.cursor()
            cur.execute(sql_command)
            row = cur.fetchone()
            print "Record loaded:", row            
        except:
            print "Getting data from db failed:", sys.exc_info()
            return
        return row
 
    def handle_single_record(self, row):
        print "Handling record"
        try:
            geometry = [row[0], row[1], row[2]]
            tmp = os.path.join(self.temp_dir, "tmp.txt")
            with open(tmp, 'wb') as f:
                f.write(row[3])
            with gzip.open(tmp, 'rb') as f:
                file_content = f.read()
            decoded_data = self.mvt.decode(file_content)
            os.remove(tmp)
            print "Decoding successful"                        
        except:
            print "decoding data with mapbox_vector_tile failed", sys.exc_info()
            return
        self._write_features(decoded_data, geometry)

        for value in self._geo_type_options:
            file_src = self.unique_file_name
            with open(file_src, "w") as f:
                json.dump(self._json_data[self._geo_type_options[value]], f)
            self._load_layer(file_src)

    def _load_layer(self, json_src):
        # load the created geojson into qgis
        name = self._mbtile_id
        layer = QgsVectorLayer(json_src, name, "ogr")
        QgsMapLayerRegistry.instance().addMapLayer(layer)

    def _create_layer(self):
        # create a layer for each type
        for value in self._geo_type_options:
            self._json_data[self._geo_type_options[value]] = {"type": "FeatureCollection", "crs":
                {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::3857"}}, "features": []}

    def _write_features(self, decoded_data, geometry):
        print "Now creating proper GeoJSON"
        # iterate through all the features of the data and build proper gejson conform objects.
        for name in decoded_data:
            for index, value in enumerate(decoded_data[name]['features']):
                data, geo_type = self._build_object(decoded_data[name]["features"][index], geometry)
                if data:
                    self._json_data[geo_type]["features"].append(data)
        #print self._json_data

    def _build_object(self, data, geometry):
        #  single feature structure
        geo_type = self._geo_type_options[data["type"]]
        coordinates = self._mercator_geometry(data["geometry"], geometry, 0)
        if data["type"] == 2 and self._counter > 0:
            # if there it is a MultiLineString, the counter will be greater than zero. return None
            self._counter = 0
            self._bool = True
            return None, geo_type
        if data["type"] == 1:
            # Due to mercator_geometrys nature, the point will be displayed in a List "[[]]", remove the outer bracket.
            coordinates = coordinates[0]
        if data["type"] == 3 and self._counter == 0:
            # If there is not a polygon in a polygon, one bracket will be missing.
            coordinates = [coordinates]
        feature = {
            "type": "Feature",
            "geometry": {
                "type": geo_type,
                "coordinates": coordinates
            },
            "properties": data["properties"]
        }
        self._counter = 0
        self._bool = True
        return feature, geo_type

    def _mercator_geometry(self, coordinates, geometry, counter):
        # recursively iterate through all the points and create an array,
        tmp = []

        for index, value in enumerate(coordinates):
            if isinstance(coordinates[index][0], int):
                tmp.append(self._calculate_geometry(self, coordinates[index], geometry))
            else:
                tmp.append(self._mercator_geometry(coordinates[index], geometry, counter + 1))
        if self._bool:
            self._counter = counter
            self._bool = False
        return tmp

    @staticmethod
    def _calculate_geometry(self, coordinates, geometry):
        # calculate the mercator geometry using external library
        # geometry:: 0: zoom, 1: easting, 2: northing
        tmp = GlobalMercator().TileBounds(geometry[1], geometry[2], geometry[0])
        delta_x = tmp[2] - tmp[0]
        delta_y = tmp[3] - tmp[1]
        merc_easting = int(tmp[0] + delta_x / self._extent * coordinates[0])
        merc_northing = int(tmp[1] + delta_y / self._extent * coordinates[1])
        return [merc_easting, merc_northing]

    @property
    def unique_file_name(self):
        unique_name = "%s.geojson" % uuid.uuid4()
        return os.path.join(self.temp_dir, unique_name)
