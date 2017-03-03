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

class _GeoTypes:
    POINT = "Point"
    LINE_STRING = "LineString"
    POLYGON = "Polygon"

GeoTypes = _GeoTypes()

class VtReader:  
    geo_types = {
        1: GeoTypes.POINT, 
        2: GeoTypes.LINE_STRING, 
        3: GeoTypes.POLYGON}  

    json_template = {
        GeoTypes.POINT: {}, 
        GeoTypes.LINE_STRING: {}, 
        GeoTypes.POLYGON: {}}  

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
            #print "Geom: ", geometry
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
        #print decoded_data

        self.write_features(decoded_data, geometry)
        for value in self.geo_types:
            file_src = self.create_unique_file_name()
            with open(file_src, "w") as f:
                json.dump(self.json_template[self.geo_types[value]], f)
            self.add_vector_layer(file_src, self.geo_types[value])

    def add_vector_layer(self, json_src, layer_name):
        # load the created geojson into qgis
        layer = QgsVectorLayer(json_src, layer_name, "ogr")
        QgsMapLayerRegistry.instance().addMapLayer(layer)

    def _create_layer(self):
        # create a layer for each type
        print "create a layer for each type"
        for value in self.geo_types:
            self.json_template[self.geo_types[value]] = {
                "type": "FeatureCollection", 
                "crs": { # crs = coordinate reference system
                    "type": "name", 
                    "properties": {
                        "name": "urn:ogc:def:crs:EPSG::3857"
                        }
                }, 
                        "features": []
            }
        print "Template: ", self.json_template

    def write_features(self, decoded_data, geometry):
        print "Now creating proper GeoJSON"
        # iterate through all the features of the data and build proper gejson conform objects.
        for name in decoded_data:
            print "Handle features of layer: ", name
            for index, feature in enumerate(decoded_data[name]['features']):
                data, geo_type = self.create_feature_json(feature, geometry)
                if data:
                    #print "feature: ", data
                    self.json_template[geo_type]["features"].append(data)
                
                # TODO: remove the break after debugging
                #break
        #print self.json_template

    def create_feature_json(self, data, geometry):
        data_type = data["type"]
        #  single feature structure
        geo_type = self.geo_types[data_type]
        coordinates = self._mercator_geometry(geo_type, data["geometry"], geometry, 0)        

        if geo_type == GeoTypes.POINT:
            assert data_type == 1
            # Due to mercator_geometrys nature, the point will be displayed in a List "[[]]", remove the outer bracket.
            coordinates = coordinates[0]
        if geo_type == GeoTypes.POLYGON and self._counter == 0:
            assert data_type == 3
            # If there is not a polygon in a polygon, one bracket will be missing.
            coordinates = [coordinates]

        feature = None
        # if there is no MultiLineString create a new feature
        # if there IS a MultiLineString the counter will be greater than zero
        if data_type != 2 or self._counter == 0:
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

    def _mercator_geometry(self, geo_type, coordinates, geometry, counter):
        # print "mercator iteration {}".format(counter)
        # print "-- type: ", geo_type
        # print "-- geometry: ", geometry
        # print "-- coordinates: ", coordinates

        # recursively iterate through all the points and create an array,
        tmp = []

        for index, coord in enumerate(coordinates):
            is_multi = not isinstance(coord[0], int)
            multi_string = "Multi" if is_multi else ""
            # print "---- coord: {} (Type: {})".format(coord, "{}{}".format(multi_string, geo_type))

            if not is_multi:
                tmp.append(self._calculate_geometry(self, coord, geometry))
            else:
                tmp.append(self._mercator_geometry(geo_type, coord, geometry, counter + 1))
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

    def create_unique_file_name(self, ending = "geojson"):
        unique_name = "{}.{}".format(uuid.uuid4(), ending)
        return os.path.join(self.temp_dir, unique_name)
