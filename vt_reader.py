import sqlite3
import sys
import os
import site
import importlib
import json
import zlib
from VectorTileHelper import VectorTile
from feature_helper import FeatureMerger
from file_helper import FileHelper
from qgis.core import QgsVectorLayer, QgsProject, QgsMapLayerRegistry, QgsVectorFileWriter
from GlobalMapTiles import GlobalMercator
from log_helper import info, warn, critical, debug


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
        "transportation",
        "transportation_name",
        "housenumber",
        "building",
        "place",
        "aeroway",
        "boundary",
        "park",
        "water_name",
        "waterway",
        "water",
        "landcover",
        "landuse"
    ]

    _extent = 4096
    _file_path = "{}/sample data/zurich_switzerland.mbtiles".format(FileHelper.get_directory())
    _layers_to_dissolve = []

    def __init__(self, iface):
        self.iface = iface
        self._import_libs()
        self._counter = 0
        self._bool = True
        self._mbtile_id = "name"
        self.features_by_path = {}
        self.qgis_layer_groups_by_feature_path = {}

    def reinit(self):
        """
         * Reinitializes the VtReader
         >> Cleans the temp directory
         >> Cleans the feature cache
         >> Cleans the qgis group cache
        """

        FileHelper.clear_temp_dir()
        self.features_by_path = {}
        self.qgis_layer_groups_by_feature_path = {}

    @staticmethod
    def _get_empty_feature_collection():
        """
         * Returns an empty GeoJSON FeatureCollection
        """
        from geojson import FeatureCollection
        crs = {  # crs = coordinate reference system
            "type": "name",
            "properties": {
                    "name": "urn:ogc:def:crs:EPSG::3857"}}
        return FeatureCollection([], crs=crs)

    def _import_libs(self):
        """
         * Imports the external libraries that are required by this plugin
        """

        site.addsitedir(os.path.join(FileHelper.get_temp_dir(), '/ext-libs'))
        self._import_library("google.protobuf")
        self.mvt = self._import_library("mapbox_vector_tile")
        self.geojson = self._import_library("geojson")

    def _import_library(self, lib):
        print "importing: ", lib
        module = importlib.import_module(lib)
        print "import successful"
        return module

    def do_work(self, zoom_level):
        self.reinit()
        self._connect_to_db()
        tile_data_tuples = self._load_tiles_from_db(zoom_level)
        # mask_level = self._get_mask_layer_id()
        # if mask_level:
        #     mask_layer_data = self._load_tiles_from_db(mask_level)
        #     tile_data_tuples.extend(mask_layer_data)
        tiles = self._decode_all_tiles(tile_data_tuples)
        self._process_tiles(tiles)
        self._create_qgis_layer_hierarchy()
        print("Import complete!")

    def _connect_to_db(self):
        """
         * Since an mbtile file is a sqlite database, we can connect to it
        """

        try:
            self.conn = sqlite3.connect(self._file_path)
            self.conn.row_factory = sqlite3.Row
            print "Successfully connected to db"
        except:
            print "Db connection failed:", sys.exc_info()
            return

    def _get_mask_layer_id(self):
        sql_command = "select value as 'masklevel' from metadata where name = 'maskLevel'"
        mask_level = None
        rows = self._get_from_db(sql=sql_command)
        if rows:
            mask_level = rows[0]["masklevel"]

        return mask_level

    def _load_tiles_from_db(self, zoom_level):
        print("Reading tiles of zoom level {}".format(zoom_level))
        if zoom_level == 14:
            # sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles WHERE zoom_level = {} and tile_row >= 10640 and tile_row <= 10645 and tile_column>=8580 and tile_column<= 8582;".format(zoom_level)
            sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles WHERE zoom_level = {} LIMIT 3;".format(zoom_level)
        else:
            sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles WHERE zoom_level = {};".format(zoom_level)
        # sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles WHERE zoom_level = {} LIMIT 10;".format(zoom_level)

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
        for tile_data_tuple in tiles_with_encoded_data:
            tile = tile_data_tuple[0]
            encoded_data = tile_data_tuple[1]
            tile.decoded_data = self._decode_binary_tile_data(encoded_data)
            tiles.append(tile)
        return tiles

    def _process_tiles(self, tiles):
        total_nr_tiles = len(tiles)
        print "Processing {} tiles".format(total_nr_tiles)
        for index, tile in enumerate(tiles):
            self._write_features(tile)
            print "Progress: {0:.1f}%".format(100.0 / total_nr_tiles * (index + 1))

    def _decode_binary_tile_data(self, data):
        try:
            # The offset of 32 signals to the zlib header that the gzip header is expected but skipped.
            file_content = zlib.decompress(data, 32 + zlib.MAX_WBITS)
            decoded_data = self.mvt.decode(file_content)
        except:
            print "decoding data with mapbox_vector_tile failed", sys.exc_info()
            return
        return decoded_data

    def _create_qgis_layer_hierarchy(self):
        """
         * Creates a hierarchy of groups and layers in qgis
        """
        print("Creating hierarchy in qgis")
        print("Layers to dissolve: {}".format(self._layers_to_dissolve))
        root = QgsProject.instance().layerTreeRoot()
        group_name = os.path.splitext(os.path.basename(self._file_path))[0]
        root_group = root.addGroup(group_name)
        feature_paths = sorted(self.features_by_path.keys(), key=lambda path: VtReader._get_feature_sort_id(path))
        for feature_path in feature_paths:
            target_group, layer_name = self._get_group_for_path(feature_path, root_group)
            feature_collection = self.features_by_path[feature_path]
            file_src = FileHelper.get_unique_file_name()
            with open(file_src, "w") as f:
                json.dump(feature_collection, f)
            layer, invalid_layer = self._add_vector_layer(file_src, layer_name, target_group, feature_path, add_invalid_layer=False)
            if invalid_layer:
                debug("invalid layer: {}".format(invalid_layer.source()))
                new_feature_collection = self._fix_layer(layer.source(), invalid_layer.source())
                new_file_src = FileHelper.get_unique_file_name()
                with open(new_file_src, "w") as f:
                    json.dump(new_feature_collection, f)
                debug("Fixed layer: {}".format(new_file_src))
                layer, invalid_layer = self._add_vector_layer(new_file_src, layer_name, target_group, feature_path, add_invalid_layer=True)
                VtReader._load_named_style(layer)
            elif layer:
                VtReader._load_named_style(layer)
            else:
                raise "What just happened?"

    @staticmethod
    def _fix_layer(valid_layer_source, invalid_layer_source):
        debug("Valid features in: {}", valid_layer_source)
        debug("Invalid features in: {}", invalid_layer_source)

        new_feature_collection = VtReader._get_empty_feature_collection()

        with open(invalid_layer_source) as data_file:
            feature_collection_invalid = json.load(data_file)
        with open(valid_layer_source) as data_file:
            feature_collection = json.load(data_file)

        feature_nrs = []
        feature_nrs_invalid = []
        for f in feature_collection_invalid["features"]:
            feature_nrs_invalid.append(f["properties"]["featureNr"])

        for f in feature_collection["features"]:
            nr = f["properties"]["featureNr"]
            if nr not in feature_nrs_invalid:
                # debug("this feature is valid: {}".format(nr))
                feature_nrs.append(nr)
                new_feature_collection["features"].append(f)

        for feature in feature_collection_invalid["features"]:
            props = feature["properties"]
            nr = props["featureNr"]
            debug("now splitting feature: {}".format(nr))
            geometry = feature["geometry"]
            geo_type = geometry["type"]
            coords = geometry["coordinates"]
            nr_new_features = len(coords)
            debug("{} features will result from split".format(nr_new_features))

            for index, c in enumerate(coords):
                newprops = props.copy()
                newprops["featureNr"] = int("{}{}".format(nr, index))
                feature_json = VtReader._create_geojson_feature_from_coordinates(geo_type, [c], newprops)
                new_feature_collection["features"].append(feature_json)

        return new_feature_collection

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
            style_name = "{}.qml".format(layer.name())
            style_path = os.path.join(FileHelper.get_directory(), "styles/{}".format(style_name))
            if os.path.isfile(style_path):
                res = layer.loadNamedStyle(style_path)
                if res[1]:  # Style loaded
                    layer.setCustomProperty("layerStyle", style_path)
                    print("Style successfully applied: {}".format(style_name))
        except:
            print("Loading style failed: {}".format(sys.exc_info()))

    def _add_vector_layer(self, json_src, layer_name, layer_target_group, feature_path, add_invalid_layer=False):
        """
         * Creates a QgsVectorLayer and adds it to the group specified by layer_target_group
         * Invalid geometries will be removed during the process of merging features over tile boundaries
        """

        invalid_layer = None
        layer = QgsVectorLayer(json_src, layer_name, "ogr")
        if feature_path in self._layers_to_dissolve:
            remove_invalid = not add_invalid_layer
            dissolved_layer, invalid = FeatureMerger().merge_features(layer, remove_invalid_features=remove_invalid)
            if invalid:
                invalid_layer = invalid
            elif dissolved_layer:
                layer = dissolved_layer
                layer.setName(layer_name)

        if not invalid_layer or add_invalid_layer:
            QgsMapLayerRegistry.instance().addMapLayer(layer, False)
            layer_target_group.addLayer(layer)

        return layer, invalid_layer

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

                    self.features_by_path[feature_path].features.append(geojson_feature)

                    if geo_type in [GeoTypes.POLYGON] and feature_path not in self._layers_to_dissolve:
                        self._layers_to_dissolve.append(feature_path)

                    # todo: remove after testing
                    # break

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

        # feature_path += "_{}".format(zoom_level)
        return feature_path

    total_feature_count = 0

    @staticmethod
    def _create_geojson_feature(feature, tile):
        """
        Creates a proper GeoJSON feature for the specified feature
        """

        geo_type = VtReader.geo_types[feature["type"]]
        coordinates = feature["geometry"]

        # print "coords before: ", coordinates
        # coordinates = VtReader._map_coordinates_recursive(coordinates=coordinates, func=lambda coords: coords)
        coordinates = VtReader._map_coordinates_recursive(coordinates=coordinates, func=lambda coords: VtReader._calculate_geometry(coords, tile))
        # print "   coords after: ", coordinates

        # if geo_type == GeoTypes.POINT:
        #     # points = []
        #     # for p in coordinates:
        #     #     points.append(p[0])
        #     coordinates = coordinates[0]
        # elif geo_type == GeoTypes.LINE_STRING:
        #     pass
        # elif geo_type == GeoTypes.POLYGON:
        #     # coordinates = VtReader._classify_rings(coordinates)
        #     pass
        #
        # is_multi = False
        # if len(coordinates) == 1:
        #     coordinates = coordinates[0]
        # else:
        #     is_multi = True

        # is_multi = len(coordinates) > 1
        # is_multi = False
        # if len(coordinates) == 1:
        #     coordinates = coordinates[0]
        # else:
        #     is_multi = True

        # if geo_type == GeoTypes.POLYGON:
        #     coordinates = VtReader._classify_rings(coordinates)

        # coordinates = VtReader.reduce_nesting(coordinates)

        if geo_type == GeoTypes.POINT:
            # Due to mercator_geometrys nature, the point will be displayed in a List "[[]]", remove the outer bracket.
            coordinates = coordinates[0]

        is_multi = VtReader._get_is_multi(geo_type, coordinates)
        # if not is_multi:
        #     coordinates = coordinates[0]

        # is_multi = False

        # if geo_type == GeoTypes.POINT:
        #     # Due to mercator_geometrys nature, the point will be displayed in a List "[[]]", remove the outer bracket.
        #     coordinates = coordinates[0]

        properties = feature["properties"]
        properties["zoomLevel"] = tile.zoom_level
        properties["featureNr"] = VtReader.total_feature_count
        VtReader.total_feature_count += 1

        feature_json = VtReader._create_geojson_feature_from_coordinates(geo_type, coordinates, properties, is_multi)

        return feature_json, geo_type

    @staticmethod
    def _get_is_multi(geo_type, coordinates):
        is_multi = False
        if geo_type == GeoTypes.POINT:
            is_multi = len(coordinates) > 1 and all(isinstance(c, int) for c in coordinates)
        elif geo_type in [GeoTypes.LINE_STRING, GeoTypes.POLYGON]:
            # array of arrays
            is_multi = len(coordinates) > 1 and not all(isinstance(c, int) for c in coordinates)

        return is_multi


    @staticmethod
    def _create_geojson_feature_from_coordinates(geo_type, coordinates, properties, is_multi):
        # from geojson import Feature, Point, Polygon, LineString, utils, MultiPoint, MultiPolygon, MultiLineString

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


        # if geo_type == GeoTypes.POINT:
        #     if is_multi:
        #         geometry = Point(coordinates)
        #     else:
        #         geometry = Point(coordinates)
        # elif geo_type == GeoTypes.POLYGON:
        #     if is_multi:
        #         geometry = MultiPolygon(coordinates)
        #     else:
        #         geometry = Polygon(coordinates)
        # elif geo_type == GeoTypes.LINE_STRING:
        #     if is_multi:
        #         geometry = MultiLineString(coordinates)
        #     else:
        #         geometry = LineString(coordinates)
        # else:
        #     raise Exception("Unexpected geo_type: {}".format(geo_type))
        #
        # feature_json = Feature(geometry=geometry, properties=properties)
        #
        # return feature_json

    @staticmethod
    def _classify_rings(rings):
        """
         * classifies an array of rings into polygons with outer rings and holes
        :param rings:
        :return:
        """

        if len(rings) <= 1:
            return [rings]

        polygons = []
        polygon = []
        ccw = None
        for ring in rings:
            area = VtReader._signed_area(ring)
            if area == 0:
                continue

            if not ccw:
                ccw = area < 0

            if ccw == area < 0:
                if polygon:
                    polygons.append(polygon)
                polygon = [ring]
            else:
                if not polygon:
                    polygon = []
                polygon.append(ring)

        if polygon:
            polygons.append(polygon)
        return polygons

    @staticmethod
    def _signed_area(ring):
        area_sum = 0
        i = 0
        ring_len = len(ring)
        j = ring_len - 1
        while i < ring_len:
            p1 = ring[i]
            p2 = ring[j]
            area_sum += (p2[0] - p1[0]) * (p1[1] + p2[1])
            j = i
            i += 1
        return area_sum

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
    def reduce_nesting(coordinates):
        """
         * Removes unnecessary nesting from a recursive array of coordinates, otherwise the GeoJSON feature could be invalid
        """
        tmp = []
        for coord in coordinates:
            if isinstance(coord, int):
                tmp.append(coord)
            else:
                is_coordinate_tuple = len(coord) == 2 and all(isinstance(c, int) for c in coord)
                if is_coordinate_tuple:
                    tmp.append(coord)
                else:
                    if len(coord) == 1 and not isinstance(coord[0], int):
                        tmp.append(coord[0])
                    else:
                        tmp.append(VtReader.reduce_nesting(coord))
        return tmp


    @staticmethod
    def _calculate_geometry(coordinates, tile):
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
