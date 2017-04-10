import sqlite3
import sys
import os
import json
import numbers
from VectorTileHelper import VectorTile
from feature_helper import FeatureMerger
from file_helper import FileHelper
from qgis.core import QgsVectorLayer, QgsProject, QgsMapLayerRegistry
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
    _zoom_level_delimiter = "*"

    def __init__(self, iface, mbtiles_path, progress_handler):
        """
         * The mbtiles_path can also be an URL in zxy format: z=zoom, x=tile column, y=tile row
        :param iface: 
        :param mbtiles_path: 
        """

        self.iface = iface
        self.progress_handler = progress_handler
        self.is_web_source = mbtiles_path.lower().startswith("http://")
        if self.is_web_source:
            content = FileHelper.load_url(url=mbtiles_path, size=2)
            if not FileHelper.is_mapbox_pbf(content=content):
                warn("The specified url doesnt provide valid Mapbox pbf")
                raise RuntimeError("This is not a valid url")
            else:
                debug("The url provides valid Mapbox pbf")
        else:
            is_sqlite_db = FileHelper.is_sqlite_db(mbtiles_path)
            if not is_sqlite_db:
                raise RuntimeError("The file '{}' is not a valid Mapbox vector tile file and cannot be loaded.".format(mbtiles_path))

        self._current_mbtiles_path = mbtiles_path
        self.conn = None
        self.max_zoom = None
        self.min_zoom = None
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

    def _update_progress(self, title=None, show_dialog=None, progress=None, max_progress=None, msg=None):
        if self.progress_handler:
            self.progress_handler(title, progress, max_progress, msg, show_dialog)

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

    def load_vector_tiles(self, zoom_level, load_mask_layer=False, merge_tiles=True, apply_styles=True, tilenumber_limit=None):
        """
         * Loads the vector tiles from either a file or a URL and adds them to QGIS
        :param zoom_level: The zoom level to load
        :param load_mask_layer: If True the mask layer will also be loaded
        :param merge_tiles: If True neighbouring tiles and features will be merged
        :param apply_styles: If True the default styles will be applied
        :param tilenumber_limit: If set then the nr of tiles being loaded will be restricted
        :return: 
        """

        self._update_progress(title="Loading '{}'".format(os.path.basename(self._current_mbtiles_path)))
        self._update_progress(show_dialog=True)
        mbtiles_path = self._current_mbtiles_path
        debug("Loading vector tiles: {}", mbtiles_path)
        self.reinit()

        tile_data_tuples = []
        if self.is_web_source:
            tile_data_tuples.append(self._load_tiles_from_url())
        else:
            tile_data_tuples = self._load_tiles_from_file(zoom_level, max_tiles=tilenumber_limit)
            if load_mask_layer and not self.is_web_source:
                mask_level = self._get_mask_level()
                if mask_level:
                    mask_layer_data = self._load_tiles_from_file(mask_level, max_tiles=tilenumber_limit)
                    tile_data_tuples.extend(mask_layer_data)
        tiles = self._decode_all_tiles(tile_data_tuples)
        self._process_tiles(tiles)
        self._create_qgis_layer_hierarchy(merge_features=merge_tiles, mbtiles_path=mbtiles_path, apply_styles=apply_styles)
        self._close_connection()
        self._update_progress(show_dialog=False)
        info("Import complete!")

    def _load_tiles_from_url(self):
        content = FileHelper.load_url(self._current_mbtiles_path)
        tile = VectorTile(14, 8568, 10636)
        return tile, content

    def _close_connection(self):
        """
         * Closes the current db connection
        :return: 
        """
        if self.conn:
            try:
                self.conn.close()
                debug("Connection closed")
            except:
                warn("Closing connection failed: {}".format(sys.exc_info()))
        self.conn = None

    def _connect_to_db(self):
        """
         * Since an mbtile file is a sqlite database, we can connect to it
        """
        debug("Connecting to: {}", self._current_mbtiles_path)
        try:
            self.conn = sqlite3.connect(self._current_mbtiles_path)
            self.conn.row_factory = sqlite3.Row
            debug("Successfully connected")
        except:
            critical("Db connection failed:", sys.exc_info())
            return

    def _get_mask_level(self):
        """
         * Returns the mask level from the metadata table
        :return: 
        """
        return self._get_metadata_value("maskLevel")

    def get_max_zoom(self):
        """
         * Returns the maximum zoom that is found in either the metadata or the tile table
        :return: 
        """
        if not self.max_zoom:
            self.max_zoom = self._get_zoom(max_zoom=True)
        return self.max_zoom

    def get_min_zoom(self):
        """
         * Returns the minimum zoom that is found in either the metadata or the tile table
        :return: 
        """
        if not self.min_zoom:
            self.min_zoom = self._get_zoom(max_zoom=False)
        return self.min_zoom

    def _get_zoom(self, max_zoom=True):
        if max_zoom:
            field_name = "maxzoom"
        else:
            field_name = "minzoom"
        zoom = self._get_metadata_value(field_name)
        if not zoom:
            zoom = self._get_zoom_from_tiles_table(max_zoom=max_zoom)
        if zoom:
            zoom = int(zoom)
        return zoom

    def _get_zoom_from_tiles_table(self, max_zoom=True):
        if max_zoom:
            order = "desc"
        else:
            order = "asc"

        query = ("select zoom_level as 'zoom_level'"
                 "from tiles"
                 "order by zoom_level {}"
                 "limit 1").format(order)
        return self._get_single_value(sql_query=query, field_name="zoom_level")

    def _get_metadata_value(self, field_name):
        debug("Loading metadata value '{}'", field_name)
        sql = "select value as '{0}' from metadata where name = '{0}'".format(field_name)
        return self._get_single_value(sql_query=sql, field_name=field_name)

    def _get_single_value(self, sql_query, field_name):
        """
         * Helper function that can be used to safely load a single value from the db
         * Returns the value or None if result is empty or execution of query failed
        :param sql_query: 
        :param field_name: 
        :return: 
        """
        value = None
        try:
            rows = self._get_from_db(sql=sql_query)
            if rows:
                value = rows[0][field_name]
                debug("Value is: {}".format(value))
        except:
            critical("Loading metadata value '{}' failed: {}", field_name, sys.exc_info())
        return value

    def _load_tiles_from_file(self, zoom_level, max_tiles):
        info("Reading tiles of zoom level {}", zoom_level)

        where_clause = ""
        if zoom_level:
            where_clause = "WHERE zoom_level = {}".format(zoom_level)

        limit = ""
        if max_tiles:
            limit = "LIMIT {}".format(max_tiles)

        sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles {} {};".format(where_clause, limit)

        tile_data_tuples = []
        rows = self._get_from_db(sql=sql_command)
        for row in rows:
            tile_data_tuples.append(self._create_tile(row))
        return tile_data_tuples

    def is_mapbox_vector_tile(self):
        """
         * A .mbtiles file is a Mapbox Vector Tile if the binary tile data is gzipped.
        :return:
        """
        debug("Checking if file corresponds to Mapbox format (i.e. gzipped)")
        is_mapbox_pbf = False
        try:
            tile_data_tuples = self._load_tiles_from_file(max_tiles=1, zoom_level=None)
            if len(tile_data_tuples) == 1:
                undecoded_data = tile_data_tuples[0][1]
                if undecoded_data:
                    is_mapbox_pbf = FileHelper.is_mapbox_pbf(undecoded_data)
                    if is_mapbox_pbf:
                        debug("File is valid mbtiles")
                    else:
                        debug("pbf is not gzipped")
        except:
            warn("Something went wrong. This file doesn't seem to be a Mapbox Vector Tile. {}", sys.exc_info())
        return is_mapbox_pbf

    @staticmethod
    def _create_tile(row):
        zoom_level = row["zoom_level"]
        tile_col = row["tile_column"]
        tile_row = row["tile_row"]
        binary_data = row["tile_data"]
        tile = VectorTile(zoom_level, tile_col, tile_row)
        return tile, binary_data

    def _get_from_db(self, sql):
        if not self.conn:
            debug("Not connected yet.")
            self._connect_to_db()
        try:
            debug("Execute SQL: {}", sql)
            cur = self.conn.cursor()
            cur.execute(sql)
            return cur.fetchall()
        except:
            critical("Getting data from db failed:", sys.exc_info())

    def _decode_all_tiles(self, tiles_with_encoded_data):
        tiles = []
        total_nr_tiles = len(tiles_with_encoded_data)
        info("Decoding {} tiles", total_nr_tiles)
        self._update_progress(progress=0, max_progress=100, msg="Loading tiles...")
        for index, tile_data_tuple in enumerate(tiles_with_encoded_data):
            tile = tile_data_tuple[0]
            encoded_data = tile_data_tuple[1]
            tile.decoded_data = self._decode_binary_tile_data(encoded_data)
            if tile.decoded_data:
                tiles.append(tile)
            progress = int(100.0 / total_nr_tiles * (index + 1))
            self._update_progress(progress=progress)
            debug("Progress: {0:.1f}%", progress)
        return tiles

    def _process_tiles(self, tiles):
        total_nr_tiles = len(tiles)
        info("Processing {} tiles", total_nr_tiles)
        self._update_progress(progress=0, max_progress=100, msg="Processing features...")
        for index, tile in enumerate(tiles):
            self._write_features(tile)
            progress = int(100.0 / total_nr_tiles * (index + 1))
            self._update_progress(progress=progress)
            debug("Progress: {0:.1f}%", progress)

    def _decode_binary_tile_data(self, data):
        try:
            file_content = GzipFile('', 'r', 0, StringIO(data)).read()
            decoded_data = mapbox_vector_tile.decode(file_content)
        except:
            critical("decoding data with mapbox_vector_tile failed", sys.exc_info())
            return
        return decoded_data

    def _create_qgis_layer_hierarchy(self, merge_features, mbtiles_path, apply_styles):
        """
         * Creates a hierarchy of groups and layers in qgis
        """
        debug("Creating hierarchy in QGIS")
        root = QgsProject.instance().layerTreeRoot()
        group_name = os.path.splitext(os.path.basename(mbtiles_path))[0]
        root_group = root.addGroup(group_name)
        feature_paths = sorted(self.features_by_path.keys(), key=lambda path: VtReader._get_feature_sort_id(path))
        self._update_progress(progress=0, max_progress=len(feature_paths), msg="Creating layers...")
        layers = []
        for index, feature_path in enumerate(feature_paths):
            target_group, layer_name = self._get_group_for_path(feature_path, root_group)
            feature_collection = self.features_by_path[feature_path]
            file_src = FileHelper.get_unique_file_name()
            with open(file_src, "w") as f:
                json.dump(feature_collection, f)
            layer = self._add_vector_layer(file_src, layer_name, target_group, feature_path, merge_features)
            layers.append(layer)
            self._update_progress(progress=index+1)

        if apply_styles:
            self._update_progress(progress=0, max_progress=len(layers), msg="Styling layers...")
            for index, layer in enumerate(layers):
                VtReader._apply_named_style(layer)
                self._update_progress(progress=index+1)

    @staticmethod
    def _get_feature_sort_id(feature_path):
        nodes = feature_path.split(".")
        sort_id = 999
        for node in nodes:
            current_node = node.split(VtReader._zoom_level_delimiter)[0]
            if current_node in VtReader.layer_sort_ids:
                sort_id = VtReader.layer_sort_ids.index(current_node)
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
    def _apply_named_style(layer):
        """
         * Looks for a styles with the same name as the layer and if one is found, it is applied to the layer
        :param layer: 
        :return: 
        """
        try:
            name = layer.name().split(VtReader._zoom_level_delimiter)[0]
            style_name = "{}.qml".format(name)
            style_path = os.path.join(FileHelper.get_plugin_directory(), "styles/{}".format(style_name))
            if os.path.isfile(style_path):
                res = layer.loadNamedStyle(style_path)
                if res[1]:  # Style loaded
                    layer.setCustomProperty("layerStyle", style_path)
                    debug("Style successfully applied: {}", style_name)
        except:
            critical("Loading style failed: {}", sys.exc_info())

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

        feature_path += "{}{}".format(VtReader._zoom_level_delimiter, zoom_level)
        return feature_path

    total_feature_count = 0

    @staticmethod
    def _create_geojson_feature(feature, tile):
        """
        Creates a proper GeoJSON feature for the specified feature
        """

        geo_type = VtReader.geo_types[feature["type"]]
        coordinates = feature["geometry"]

        coordinates = VtReader._map_coordinates_recursive(coordinates=coordinates, func=lambda coords: VtReader._transform_to_epsg3857(coords, tile))

        if geo_type == GeoTypes.POINT:
            # Due to mercator_geometrys nature, the point will be displayed in a List "[[]]", remove the outer bracket.
            coordinates = coordinates[0]

        properties = feature["properties"]
        properties["_zoomLevel"] = tile.zoom_level
        properties["_featureNr"] = VtReader.total_feature_count
        properties["_col"] = tile.column
        properties["_row"] = tile.row
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
