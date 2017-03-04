from qgis.core import *
from GlobalMapTiles import GlobalMercator

import sqlite3
import sys
import os
import site
import importlib
import uuid
import json
import glob
import zlib
from VectorTileHelper import VectorTile

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

    def reset_json_template(self):
        self.json_template = {
            GeoTypes.POINT: {}, 
            GeoTypes.LINE_STRING: {}, 
            GeoTypes.POLYGON: {}} 

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
        self.connect_to_db() 
        tiles = self.load_tiles_from_db()
        self.init_json_template()
        self.process_tiles(tiles)

    def connect_to_db(self):
        try:
            self.conn = sqlite3.connect(self.filePath)
            self.conn.row_factory = sqlite3.Row
            print "Successfully connected to db"
        except:
            print "Db connection failed:", sys.exc_info()
            return        

    def load_tiles_from_db(self):
        print "Reading data from db"
        zoom_level = 14
        sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles WHERE zoom_level = {} LIMIT 1;".format(zoom_level)
        tiles = []
        try:
            cur = self.conn.cursor()
            for row in cur.execute(sql_command):      
                zoom_level = row["zoom_level"]
                x = row["tile_column"]
                y = row["tile_row"]
                binary_data = row["tile_data"]
                decoded_data = self.decode_binary_tile_data(binary_data) 
                tile = VectorTile(zoom_level, x, y, decoded_data)
                #print "Tile: ", tile
                tiles.append(tile)
        except:
            print "Getting data from db failed:", sys.exc_info()
            return
        return tiles

    def init_json_template(self):
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
        print "template: ", self.json_template

    def process_tiles(self, tiles):
        base_template = self.json_template
        totalNrTiles = len(tiles)
        #"{} rows to process".format(len(rowSet))
        for index, tile in enumerate(tiles):
            #self.init_json_template()
            
            self.write_features(tile)
            print "Progress: {}%".format(100.0 / totalNrTiles * (index+1))

        # the layers are only created once
        # this means one vector layer per geotype will be added in qgis
        # the other option would be to call this method once per row, then we have to reinitialize the json template for each row again
        self.create_layers_for_geotypes()        

    def decode_binary_tile_data(self, data):
        try:
            # The offset of 32 signals to the zlib header that the gzip header is expected but skipped.
            file_content = zlib.decompress(data, 32 + zlib.MAX_WBITS)
            decoded_data = self.mvt.decode(file_content)                   
        except:
            print "decoding data with mapbox_vector_tile failed", sys.exc_info()
            return
        return decoded_data

    def create_layers_for_geotypes(self):
        root = QgsProject.instance().layerTreeRoot()
        myGroup1 = root.addGroup("My Group 1")
        for value in self.geo_types:
            file_src = self.create_unique_file_name()
            with open(file_src, "w") as f:
                json.dump(self.json_template[self.geo_types[value]], f)
            self.add_vector_layer(file_src, self.geo_types[value], myGroup1)

    def add_vector_layer(self, json_src, layer_name, layer_target_group):
        # load the created geojson into qgis
        layer = QgsVectorLayer(json_src, layer_name, "ogr")
        QgsMapLayerRegistry.instance().addMapLayer(layer, False)    
        layer_target_group.addLayer(layer)

    def write_features(self, tile):
        # iterate through all the features of the data and build proper gejson conform objects.
        for name in tile.decoded_data:
            print "Handle features of layer: ", name
            tile_features = tile.decoded_data[name]["features"]
            for index, feature in enumerate(tile_features):
                data, geo_type = self.create_feature_json(feature, tile)
                if data:
                    #print "feature: ", data
                    self.json_template[geo_type]["features"].append(data)
                
                # TODO: remove the break after debugging
                # print "feature: ", feature
                # print "   data: ", data
                # break
        #print self.json_template

    def create_feature_json(self, feature, tile):
        #print "feature: ", feature
        feature_type = feature["type"]
        #  single feature structure
        geo_type = self.geo_types[feature_type]

        coordinates = self._mercator_geometry(geo_type, feature["geometry"], tile, 0)

        if geo_type == GeoTypes.POINT:
            assert feature_type == 1
            # Due to mercator_geometrys nature, the point will be displayed in a List "[[]]", remove the outer bracket.
            coordinates = coordinates[0]
        if geo_type == GeoTypes.POLYGON and self._counter == 0:
            assert feature_type == 3
            # If there is not a polygon in a polygon, one bracket will be missing.
            coordinates = [coordinates]        

        feature_json = None

        # if there is no MultiLineString create a new feature
        # if there IS a MultiLineString the counter will be greater than zero and NO feature will be created
        if feature_type != 2 or self._counter == 0:
            feature_json = {
                "type": "Feature",
                "geometry": {
                    "type": geo_type,
                    "coordinates": coordinates
                },
                "properties": feature["properties"]
            }
        else:
            print "whats this.........................."
            print "feature: ", feature
            print "coordinates: ", coordinates
            feature_json = {
                "type": "Feature",
                "geometry": {
                    "type": geo_type,
                    "coordinates": coordinates
                },
                "properties": feature["properties"]
            }

        self._counter = 0
        self._bool = True
        return feature_json, geo_type

    def _mercator_geometry(self, geo_type, coordinates, tile, counter):        
        # print "mercator iteration {}".format(counter)
        # print "-- type: ", geo_type
        # print "-- geometry: ", geometry
        # print "-- coordinates: ", coordinates

        # recursively iterate through all the points and create an array,
        tmp = []

        for index, coord in enumerate(coordinates):
            is_multi = not isinstance(coord[0], int)
            multi_string = "Multi" if is_multi else ""
            # if is_multi:
            #     print "---- coord: {} (Type: {})".format(coord, "{}{}".format(multi_string, geo_type))

            if not is_multi:
                tmp.append(self._calculate_geometry(self, coord, tile))
            else:
                #print "is multi: ", coordinates
                tmp.append(self._mercator_geometry(geo_type, coord, tile, counter + 1))

        if self._bool:
            self._counter = counter
            self._bool = False
        return tmp

    @staticmethod
    def _calculate_geometry(self, coordinates, tile):
        """
        Does a mercator transformation on 
        """
        # calculate the mercator geometry using external library
        # geometry:: 0: zoom, 1: easting, 2: northing
        tmp = GlobalMercator().TileBounds(tile.column, tile.row, tile.zoom_level)
        delta_x = tmp[2] - tmp[0]
        delta_y = tmp[3] - tmp[1]
        merc_easting = int(tmp[0] + delta_x / self._extent * coordinates[0])
        merc_northing = int(tmp[1] + delta_y / self._extent * coordinates[1])
        return [merc_easting, merc_northing]

    def create_unique_file_name(self, ending = "geojson"):
        unique_name = "{}.{}".format(uuid.uuid4(), ending)
        return os.path.join(self.temp_dir, unique_name)
