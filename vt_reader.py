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

    layer_sort_ids = {
        "poi" : 0,
        "transportation" : 1,
        "transportation_name" : 2,
        "housenumber" : 3,
        "building" : 4,
        "place" : 5,
        "aeroway" : 6,        
        "boundary" : 7,
        "park" : 8,
        "water_name" : 9,
        "waterway" : 10,
        "landuse" : 11,
        "landcover" : 12
    }

    _extent = 4096    
    directory = os.path.abspath(os.path.dirname(__file__))
    temp_dir = "%s/tmp" % directory
    file_path = "%s/sample data/zurich_switzerland.mbtiles" % directory    
    
    def __init__(self, iface):
        self.iface = iface
        self.import_libs()
        self._counter = 0
        self._bool = True
        self._mbtile_id = "name"

    def reinit(self):
        """
         * Reinitializes the VtReader
         >> Cleans the temp directory
         >> Cleans the feature cache
         >> Cleans the qgis group cache
        """

        self.clear_temp_dir()
        self.features_by_path = {}
        self.qgis_layer_groups_by_feature_path = {}

    def clear_temp_dir(self):
        """
         * Removes all files from the temp_dir
        """
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)
        files = glob.glob("%s/*" % self.temp_dir)
        for f in files:
            os.remove(f)

    def get_empty_feature_collection(self):
        """
         * Returns an empty GeoJSON FeatureCollection
        """

        from geojson import FeatureCollection
        crs = { # crs = coordinate reference system
                "type": "name", 
                "properties": { 
                    "name": "urn:ogc:def:crs:EPSG::3857" } }        
        return FeatureCollection([], crs=crs)

    def import_libs(self):
        """
         * Imports the external libraries that are required by this plugin
        """

        site.addsitedir(os.path.join(self.temp_dir, '/ext-libs'))
        self.import_library("google.protobuf")
        self.mvt = self.import_library("mapbox_vector_tile")
        self.geojson = self.import_library("geojson")        

    def import_library(self, lib):
        print "importing: ", lib
        module = importlib.import_module(lib)
        print "import successful"
        return module

    def do_work(self, zoom_level):
        self.reinit()
        self.connect_to_db() 
        tile_data_tuples = self.load_tiles_from_db(zoom_level)
        tiles = self.decode_all_tiles(tile_data_tuples)
        self.process_tiles(tiles)
        self.create_qgis_layer_hierarchy()

    def connect_to_db(self):
        """
         * Since an mbtile file is a sqlite database, we can connect to it
        """

        try:
            self.conn = sqlite3.connect(self.file_path)
            self.conn.row_factory = sqlite3.Row
            print "Successfully connected to db"
        except:
            print "Db connection failed:", sys.exc_info()
            return        

    def load_tiles_from_db(self, zoom_level):
        print "Reading data from db"
        sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles WHERE zoom_level = {} LIMIT 2;".format(zoom_level)
        tile_data_tuples = []
        try:
            cur = self.conn.cursor()
            for row in cur.execute(sql_command):      
                zoom_level = row["zoom_level"]
                tile_col = row["tile_column"]
                tile_row = row["tile_row"]
                binary_data = row["tile_data"]
                tile = VectorTile(zoom_level, tile_col, tile_row)
                tile_data_tuples.append((tile, binary_data))
        except:
            print "Getting data from db failed:", sys.exc_info()
            return
        return tile_data_tuples

    def decode_all_tiles(self, tiles_with_encoded_data):
        tiles = []
        for tile_data_tuple in tiles_with_encoded_data:
            tile = tile_data_tuple[0]
            encoded_data = tile_data_tuple[1]
            tile.decoded_data = self.decode_binary_tile_data(encoded_data)
            tiles.append(tile)
        return tiles

    def process_tiles(self, tiles):
        totalNrTiles = len(tiles)
        print "Processing {} tiles".format(totalNrTiles)
        for index, tile in enumerate(tiles):          
            self.write_features(tile)
            print "Progress: {0:.1f}%".format(100.0 / totalNrTiles * (index+1))      

    def decode_binary_tile_data(self, data):
        try:
            # The offset of 32 signals to the zlib header that the gzip header is expected but skipped.
            file_content = zlib.decompress(data, 32 + zlib.MAX_WBITS)
            decoded_data = self.mvt.decode(file_content)                   
        except:
            print "decoding data with mapbox_vector_tile failed", sys.exc_info()
            return
        return decoded_data
    
    def create_qgis_layer_hierarchy(self):
        """
         * Creates a hierarchy of groups and layers in qgis
        """
        print "Creating hierarchy in qgis"
        root = QgsProject.instance().layerTreeRoot()
        group_name = os.path.splitext(os.path.basename(self.file_path))[0]
        rootGroup = root.addGroup(group_name)
        #print "all paths: ", self.features_by_path.keys()
        feature_paths = sorted(self.features_by_path.keys(), key=lambda path: self.get_sort_id(path))
        for feature_path in feature_paths:
            target_group, layer_name = self.get_group_for_path(feature_path, rootGroup)
            feature_collection = self.features_by_path[feature_path]                      
            file_src = self.create_unique_file_name()
            with open(file_src, "w") as f:
                json.dump(feature_collection, f)
            layer = self.add_vector_layer(file_src, layer_name, target_group)
            self.load_named_style(layer, feature_path.split(".")[0])

    def get_sort_id(self, feature_path):
        # print "get sort id for: ", feature_path
        first_node = feature_path.split(".")[0]
        sort_id = 999
        if first_node in self.layer_sort_ids:
            sort_id = self.layer_sort_ids[first_node]
        return sort_id

    def get_group_for_path(self, path, root_group):
        """
         * Returns the group for the specified path
         >> If the group not already exists, it will be created
         >> The path has to be delimited by '.'
         >> The last element in the path will be used as name for the vector layer, the other elements will be used to create the group hierarchy
         >> Example: The path 'zurich.poi.police' will create two groups 'zurich' and 'poi' (if not already existing) and 'police' will be returned as name for the layer to create
        """

        group_names = path.split(".")
        current_group = root_group
        current_path = ""
        target_layer_name = ""
        for index, name in enumerate(group_names):
            target_layer_name = name
            is_last = index == len(group_names)-1
            if is_last:
                break
            current_path += "."+name
            if not current_path in self.qgis_layer_groups_by_feature_path:
                self.qgis_layer_groups_by_feature_path[current_path] = self.create_group(name, current_group)
            current_group = self.qgis_layer_groups_by_feature_path[current_path]
        return current_group, target_layer_name

    def create_group(self, name, parent_group):
        new_group = parent_group.addGroup(name)
        return new_group

    def load_named_style(self, layer, root_group_name):
        style_name = "{}.qml".format(layer.name())
        # style_name = "{}.qml".format(root_group_name)
        style_path = os.path.join(self.directory, "styles/{}".format(style_name))
        if os.path.isfile(style_path):
            res = layer.loadNamedStyle(style_path)
            if res[1]: # Style loaded
                layer.setCustomProperty("layerStyle", style_path)
                print "Style successfully applied: ", style_name

    def add_vector_layer(self, json_src, layer_name, layer_target_group):
        """
         * Creates a QgsVectorLayer and adds it to the group specified by layer_target_group
        """

        # load the created geojson into qgis
        layer = QgsVectorLayer(json_src, layer_name, "ogr")
        QgsMapLayerRegistry.instance().addMapLayer(layer, False)    
        layer_target_group.addLayer(layer)    
        return layer

    def write_features(self, tile):
        # iterate through all the features of the data and build proper gejson conform objects.
        for layer_name in tile.decoded_data:
            
            print "Handle features of layer: ", layer_name
            tile_features = tile.decoded_data[layer_name]["features"]
            for index, feature in enumerate(tile_features):
                geojson_feature, geo_type = self.create_geojson_feature(feature, tile)
                if geojson_feature:
                    feature_path = self.get_feature_path(layer_name, geojson_feature)
                    if not feature_path in self.features_by_path:
                        self.features_by_path[feature_path] = self.get_empty_feature_collection()

                    self.features_by_path[feature_path].features.append(geojson_feature)
                
                # TODO: remove the break after debugging
                # print "feature: ", feature
                # print "   data: ", data
                #break

    def get_feature_class_and_subclass(self, feature):
        feature_class = None
        feature_subclass = None
        if "class" in feature.properties:
            feature_class = feature.properties["class"]
            if "subclass" in feature.properties:
                feature_subclass = feature.properties["subclass"]
                if feature_subclass == feature_class:
                    feature_subclass = None
        if feature_subclass:
            assert feature_class, "A feature with a subclass should also have a class"
        return feature_class, feature_subclass

    def get_feature_path(self, layer_name, feature):
        feature_class, feature_subclass = self.get_feature_class_and_subclass(feature) 
        feature_path = layer_name;
        if feature_class:
            feature_path += "." + feature_class
            if feature_subclass:
                feature_path += "." +feature_subclass
        return feature_path        

    def create_geojson_feature(self, feature, tile):
        """
        Creates a proper GeoJSON feature for the specified feature
        """
        from geojson import Feature, Point, Polygon, LineString

        geo_type = self.geo_types[feature["type"]]
        coordinates = feature["geometry"]
        coordinates = self.map_coordinates_recursive(coordinates, lambda coords: self._calculate_geometry(self, coords, tile))

        if geo_type == GeoTypes.POINT:
            # Due to mercator_geometrys nature, the point will be displayed in a List "[[]]", remove the outer bracket.
            coordinates = coordinates[0]
        
        geometry = None
        if geo_type == GeoTypes.POINT:            
            geometry = Point(coordinates)
        elif geo_type == GeoTypes.POLYGON:    
            geometry = Polygon(coordinates)
        elif geo_type == GeoTypes.LINE_STRING:
            geometry = LineString(coordinates)
        else:
            raise Exception("Unexpected geo_type: {}".format(geo_type))

        feature_json = Feature(geometry=geometry, properties=feature["properties"])

        return feature_json, geo_type

    def map_coordinates_recursive(self, coordinates, func):        
        """
        Recursively traverses the array of coordinates (depth first) and applies the specified function
        """
        tmp = []
        for coord in coordinates:          
            is_coordinate_tuple = len(coord) == 2 and all(isinstance(c, int) for c in coord)
            if is_coordinate_tuple:
                newval = func(coord)
                tmp.append(newval)
            else:
                tmp.append(self.map_coordinates_recursive(coord, func))
        return tmp

    @staticmethod
    def _calculate_geometry(self, coordinates, tile):
        """
        Does a mercator transformation on the specified coordinate tuple
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
