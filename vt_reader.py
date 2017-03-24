import sqlite3
import sys
import os
import json
import numbers
from VectorTileHelper import VectorTile
from feature_helper import FeatureMerger
from file_helper import FileHelper
from qgis.core import QgsVectorLayer, QgsProject, QgsMapLayerRegistry, QgsVectorFileWriter
from GlobalMapTiles import GlobalMercator
from log_helper import info, warn, critical, debug
from cStringIO import StringIO
from gzip import GzipFile

import mapbox_vector_tile

class _GeoTypes:
    def __init__(self):
        pass

    POINT = "Point"
    LINE_STRING = "LineString"
    POLYGON = "Polygon"

GeoTypes = _GeoTypes()


class VtReader:
    geo_types = {
        1: GeoTypes.POINT,
        2: GeoTypes.LINE_STRING,
        3: GeoTypes.POLYGON}

    layer_sort_ids = [
        "poi",
        "boundary",
        "transportation",
        "transportation_name",
        "housenumber",
        "building",
        "place",
        "aeroway",
        "park",
        "water_name",
        "waterway",
        "water",
        "landcover",
        "landuse"
    ]

    _extent = 4096
    _layers_to_dissolve = []

    def __init__(self, iface):
        self.iface = iface
        FileHelper.clear_temp_dir()
        self.reinit()

    def reinit(self):
        """
         * Reinitializes the VtReader
         >> Cleans the temp directory
         >> Cleans the feature cache
         >> Cleans the qgis group cache
        """
        self.features_by_path = {}
        self.qgis_layer_groups_by_feature_path = {}

    @staticmethod
    def _get_empty_feature_collection():
        """
         * Returns an empty GeoJSON FeatureCollection with the coordinate reference system (crs) set to EPSG3857
        """
        crs = {
            "type": "name",
            "properties": {
                    "name": "urn:ogc:def:crs:EPSG::3857"}}

        return {
            "type": "FeatureCollection",
            "crs": crs,
            "features": []}


    def load_vector_tiles(self, zoom_level, mbtiles_path, load_mask_layer=True, merge_features=True):
        debug("Loading vector tiles: {}".format(mbtiles_path))
        self.reinit()
        self._connect_to_db(mbtiles_path)
        tile_data_tuples = self._load_tiles_from_db(zoom_level)

        if load_mask_layer:
            mask_level = self._get_metadata_value("maskLevel")
            if mask_level:
                mask_layer_data = self._load_tiles_from_db(mask_level)
                tile_data_tuples.extend(mask_layer_data)
        tiles = self._decode_all_tiles(tile_data_tuples)
        self._process_tiles(tiles)
        self._create_qgis_layer_hierarchy(merge_features=merge_features, mbtiles_path=mbtiles_path)
        self._close_connection()
        print("Import complete!")

    def _close_connection(self):
        if self.conn:
            try:
                self.conn.close()
                debug("Connection closed")
            except:
                warn("Closing connection failed: {}".format(sys.exc_info()))
        self.conn = None

    def _connect_to_db(self, path):
        """
         * Since an mbtile file is a sqlite database, we can connect to it
        """
        try:
            self.conn = sqlite3.connect(path)
            self.conn.row_factory = sqlite3.Row
            print "Successfully connected to db"
        except:
            print "Db connection failed:", sys.exc_info()
            return

    def _get_metadata_value(self, field_name):
        debug("Loading metadata value '{}'".format(field_name))
        sql_command = "select value as '{0}' from metadata where name = '{0}'".format(field_name)
        value = None
        rows = self._get_from_db(sql=sql_command)
        if rows:
            value = rows[0][field_name]
            debug("Value is: {}".format(value))

        return value

    def _load_tiles_from_db(self, zoom_level):
        print("Reading tiles of zoom level {}".format(zoom_level))

        # sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles WHERE zoom_level = {} and tile_row = 10638 and tile_column=8568;".format(zoom_level)
        # sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles WHERE zoom_level = {} and tile_row = 10644 and tile_column=8581;".format(zoom_level)
        # sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles WHERE zoom_level = {} and tile_row >= 10640 and tile_row <= 10650 and tile_column>=8575 and tile_column<= 8582;".format(zoom_level)
        sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles WHERE zoom_level = {} LIMIT 5;".format(zoom_level)
        # sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles WHERE zoom_level = {};".format(zoom_level)

        tile_data_tuples = []
        rows = self._get_from_db(sql=sql_command)
        for row in rows:
            tile_data_tuples.append(self._create_tile(row))
        return tile_data_tuples

    @staticmethod
    def _create_tile(row):
        zoom_level = row["zoom_level"]
        tile_col = row["tile_column"]
        tile_row = row["tile_row"]
        binary_data = row["tile_data"]
        tile = VectorTile(zoom_level, tile_col, tile_row)
        return tile, binary_data

    def _get_from_db(self, sql):
        try:
            cur = self.conn.cursor()
            cur.execute(sql)
            return cur.fetchall()
        except:
            print "Getting data from db failed:", sys.exc_info()

    def _decode_all_tiles(self, tiles_with_encoded_data):
        tiles = []
        total_nr_tiles = len(tiles_with_encoded_data)
        print "Decoding {} tiles".format(total_nr_tiles)
        for index, tile_data_tuple in enumerate(tiles_with_encoded_data):
            tile = tile_data_tuple[0]
            encoded_data = tile_data_tuple[1]
            tile.decoded_data = self._decode_binary_tile_data(encoded_data)
            if tile.decoded_data:
                tiles.append(tile)
            print "Progress: {0:.1f}%".format(100.0 / total_nr_tiles * (index + 1))
        return tiles

    def _process_tiles(self, tiles):
        total_nr_tiles = len(tiles)
        print "Processing {} tiles".format(total_nr_tiles)
        for index, tile in enumerate(tiles):
            self._write_features(tile)
            print "Progress: {0:.1f}%".format(100.0 / total_nr_tiles * (index + 1))

    def _decode_binary_tile_data(self, data):
        try:
            file_content = GzipFile('', 'r', 0, StringIO(data)).read()
            decoded_data = mapbox_vector_tile.decode(file_content)
        except:
            print "decoding data with mapbox_vector_tile failed", sys.exc_info()
            return
        return decoded_data

    def _create_qgis_layer_hierarchy(self, merge_features, mbtiles_path):
        """
         * Creates a hierarchy of groups and layers in qgis
        """
        print("Creating hierarchy in qgis")
        print("Layers to dissolve: {}".format(self._layers_to_dissolve))
        root = QgsProject.instance().layerTreeRoot()
        group_name = os.path.splitext(os.path.basename(mbtiles_path))[0]
        root_group = root.addGroup(group_name)
        feature_paths = sorted(self.features_by_path.keys(), key=lambda path: VtReader._get_feature_sort_id(path))
        for feature_path in feature_paths:
            target_group, layer_name = self._get_group_for_path(feature_path, root_group)
            feature_collection = self.features_by_path[feature_path]
            file_src = FileHelper.get_unique_file_name()
            with open(file_src, "w") as f:
                json.dump(feature_collection, f)
            layer = self._add_vector_layer(file_src, layer_name, target_group, feature_path, merge_features)
            VtReader._load_named_style(layer)

    @staticmethod
    def _get_feature_sort_id(feature_path):
        first_node = feature_path.split(".")[0]
        sort_id = 999
        if first_node in VtReader.layer_sort_ids:
            sort_id = VtReader.layer_sort_ids.index(first_node)
        return sort_id

    def _get_group_for_path(self, path, root_group):
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
            is_last = index == len(group_names) - 1
            if is_last:
                break
            current_path += "." + name
            if current_path not in self.qgis_layer_groups_by_feature_path:
                self.qgis_layer_groups_by_feature_path[current_path] = current_group.addGroup(name)
            current_group = self.qgis_layer_groups_by_feature_path[current_path]
        return current_group, target_layer_name

    @staticmethod
    def _load_named_style(layer):
        try:
            name = layer.name().split("_")[0]
            style_name = "{}.qml".format(name)
            # style_name = "{}.qml".format(layer.name())
            style_path = os.path.join(FileHelper.get_directory(), "styles/{}".format(style_name))
            if os.path.isfile(style_path):
                res = layer.loadNamedStyle(style_path)
                if res[1]:  # Style loaded
                    layer.setCustomProperty("layerStyle", style_path)
                    print("Style successfully applied: {}".format(style_name))
        except:
            print("Loading style failed: {}".format(sys.exc_info()))

    def _add_vector_layer(self, json_src, layer_name, layer_target_group, feature_path, merge_features):
        """
         * Creates a QgsVectorLayer and adds it to the group specified by layer_target_group
         * Invalid geometries will be removed during the process of merging features over tile boundaries
        """

        layer = QgsVectorLayer(json_src, layer_name, "ogr")
        if merge_features and feature_path in self._layers_to_dissolve:
            layer = FeatureMerger().merge_features(layer)
            layer.setName(layer_name)

        QgsMapLayerRegistry.instance().addMapLayer(layer, False)
        layer_target_group.addLayer(layer)

        return layer

    def _write_features(self, tile):
        """
         * Transforms all features of the specified tile into GeoJSON and writes it into the dictionary
        :param tile:
        :return:
        """
        # iterate through all the features of the data and build proper gejson conform objects.
        for layer_name in tile.decoded_data:
            tile_features = tile.decoded_data[layer_name]["features"]
            for index, feature in enumerate(tile_features):
                geojson_feature, geo_type = VtReader._create_geojson_feature(feature, tile)
                if geojson_feature:
                    feature_path = VtReader._get_feature_path(layer_name, geojson_feature, tile.zoom_level)
                    if feature_path not in self.features_by_path:
                        self.features_by_path[feature_path] = VtReader._get_empty_feature_collection()

                    self.features_by_path[feature_path]["features"].append(geojson_feature)

                    geotypes_to_dissolve = [GeoTypes.POLYGON, GeoTypes.LINE_STRING]
                    if geo_type in geotypes_to_dissolve and feature_path not in self._layers_to_dissolve:
                        self._layers_to_dissolve.append(feature_path)

    @staticmethod
    def _get_feature_class_and_subclass(feature):
        feature_class = None
        feature_subclass = None
        properties = feature["properties"]
        if "class" in properties:
            feature_class = properties["class"]
            if "subclass" in properties:
                feature_subclass = properties["subclass"]
                if feature_subclass == feature_class:
                    feature_subclass = None
        if feature_subclass:
            assert feature_class, "A feature with a subclass should also have a class"
        return feature_class, feature_subclass

    @staticmethod
    def _get_feature_path(layer_name, feature, zoom_level):
        feature_class, feature_subclass = VtReader._get_feature_class_and_subclass(feature)
        feature_path = layer_name
        if feature_class:
            feature_path += "." + feature_class
            if feature_subclass:
                feature_path += "." + feature_subclass

        feature_path += "_{}".format(zoom_level)
        return feature_path

    total_feature_count = 0

    @staticmethod
    def _create_geojson_feature(feature, tile):
        """
        Creates a proper GeoJSON feature for the specified feature
        """

        geo_type = VtReader.geo_types[feature["type"]]
        coordinates = feature["geometry"]

        # # todo: remove after testing
        # if geo_type != GeoTypes.POLYGON:
        #     return None, None

        coordinates = VtReader._map_coordinates_recursive(coordinates=coordinates, func=lambda coords: VtReader._transform_to_epsg3857(coords, tile))

        if geo_type == GeoTypes.POINT:
            # Due to mercator_geometrys nature, the point will be displayed in a List "[[]]", remove the outer bracket.
            coordinates = coordinates[0]

        properties = feature["properties"]
        properties["zoomLevel"] = tile.zoom_level
        properties["featureNr"] = VtReader.total_feature_count
        properties["col"] = tile.column
        properties["row"] = tile.row
        VtReader.total_feature_count += 1

        feature_json = VtReader._create_geojson_feature_from_coordinates(geo_type, coordinates, properties)

        return feature_json, geo_type

    @staticmethod
    def _get_is_multi(geo_type, coordinates):
        if geo_type == GeoTypes.POINT:
            is_single = len(coordinates) == 2 and all(isinstance(c, int) for c in coordinates)
            return not is_single
        elif geo_type == GeoTypes.LINE_STRING:
            is_array_of_tuples = all(len(c) == 2 and all(isinstance(ci, int) for ci in c) for c in coordinates)
            is_single = is_array_of_tuples
            return not is_single
        elif geo_type == GeoTypes.POLYGON:
            is_multi = VtReader.get_array_depth(coordinates, 0) >= 2
            return is_multi

        return False

    @staticmethod
    def get_array_depth(arr, depth):
        if all(isinstance(c, numbers.Real) for c in arr[0]):
            return depth
        else:
            depth += 1
            return VtReader.get_array_depth(arr[0], depth)

    @staticmethod
    def _create_geojson_feature_from_coordinates(geo_type, coordinates, properties):

        is_multi = VtReader._get_is_multi(geo_type, coordinates)

        type_string = geo_type
        if is_multi:
            type_string = "Multi{}".format(geo_type)

        feature_json = {
            "type": "Feature",
            "geometry": {
                "type": type_string,
                "coordinates": coordinates
            },
            "properties": properties
        }

        return feature_json

    @staticmethod
    def _map_coordinates_recursive(coordinates, func):
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
                tmp.append(VtReader._map_coordinates_recursive(coord, func))
        return tmp

    @staticmethod
    def _transform_to_epsg3857(coordinates, tile):
        """
        Does a mercator transformation on the specified coordinate tuple
        """
        # calculate the mercator geometry using external library
        # geometry:: 0: zoom, 1: easting, 2: northing
        tmp = GlobalMercator().TileBounds(tile.column, tile.row, tile.zoom_level)
        delta_x = tmp[2] - tmp[0]
        delta_y = tmp[3] - tmp[1]
        merc_easting = int(tmp[0] + delta_x / VtReader._extent * coordinates[0])
        merc_northing = int(tmp[1] + delta_y / VtReader._extent * coordinates[1])
        return [merc_easting, merc_northing]
