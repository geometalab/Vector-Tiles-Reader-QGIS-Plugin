#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
import numbers
import math

from log_helper import info, warn, critical, debug, remove_key
from PyQt4.QtGui import QApplication
from tile_helper import get_all_tiles, change_zoom, get_code_from_epsg
from feature_helper import FeatureMerger
from file_helper import FileHelper
from qgis.core import QgsVectorLayer, QgsProject, QgsMapLayerRegistry, QgsExpressionContextUtils
from PyQt4.QtGui import QMessageBox
from cStringIO import StringIO
from gzip import GzipFile
from tile_source import ServerSource, MBTilesSource

from mp_helper import decode_tile

import multiprocessing as mp
import platform

if platform.system() == "Windows":
    # OSGeo4W does not bundle python in exec_prefix for python
    path = os.path.abspath(os.path.join(sys.exec_prefix, '../../bin/pythonw.exe'))
    mp.set_executable(path)
    sys.argv = [None]


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

    cartographic_layer_ordering = [
        "place",
        "mountain_peak",
        "housenumber",
        "water_name",
        "transportation_name",
        "poi",
        "boundary",
        "transportation",
        "building",
        "aeroway",
        "park",
        "water",
        "waterway",
        "landcover",
        "landuse"
    ]

    _extent = 4096  # this applies always for Mapbox tiles (see: https://github.com/tilezen/mapbox-vector-tile)
    _layers_to_dissolve = []
    _zoom_level_delimiter = "*"

    _styles = FileHelper.get_styles()

    def __init__(self, iface, path_or_url, progress_handler):
        """
         * The mbtiles_path can also be an URL in zxy format: z=zoom, x=tile column, y=tile row
        :param iface: 
        :param path_or_url: 
        """
        if not path_or_url:
            raise RuntimeError("The datasource is required")

        is_web_source = path_or_url.lower().startswith("http://") or path_or_url.lower().startswith("https://")
        if is_web_source:
            self.source = ServerSource(url=path_or_url)
        else:
            self.source = MBTilesSource(path=path_or_url)
        self.source.set_progress_handler(self._update_progress)

        FileHelper.assure_temp_dirs_exist()
        self.iface = iface
        self.cartographic_ordering_enabled = True
        self.progress_handler = progress_handler
        self.feature_collections_by_layer_path = {}
        self._qgis_layer_groups_by_name = {}
        self.cancel_requested = False
        self._loaded_pois_by_id = {}

    def _update_progress(self, title=None, show_dialog=None, progress=None, max_progress=None, msg=None):
        if self.progress_handler:
            self.progress_handler(title, progress, max_progress, msg, show_dialog)

    def _get_empty_feature_collection(self, zoom_level, layer_name):
        """
         * Returns an empty GeoJSON FeatureCollection with the coordinate reference system (crs) set to EPSG3857
        """
        # todo: when improving CRS handling: the correct CRS of the source has to be set here

        source_crs = self.source.crs()
        if source_crs:
            epsg_id = get_code_from_epsg(source_crs)
        else:
            epsg_id = 3857

        crs = {
            "type": "name",
            "properties": {
                    "name": "urn:ogc:def:crs:EPSG::{}".format(epsg_id)}}

        return {
            "tiles": [],
            "source": self.source.name(),
            "layer": layer_name,
            "zoom_level": zoom_level,
            "type": "FeatureCollection",
            "crs": crs,
            "features": []}

    def cancel(self):
        """
         * Cancels the loading process.
        :return: 
        """
        self.cancel_requested = True
        if self.source:
            self.source.cancel()

    def _get_tile_cache_name(self, zoom_level, col, row):
        return FileHelper.get_cached_tile_file_name(self.source.name(), zoom_level, col, row)

    def load_tiles(self, zoom_level, layer_filter, load_mask_layer=False, merge_tiles=True, apply_styles=True, max_tiles=None,
                   bounds=None, limit_reacher_handler=None):
        """
         * Loads the vector tiles from either a file or a URL and adds them to QGIS
        :param zoom_level: The zoom level to load
        :param layer_filter: A list of layers. If any layers are set, only these will be loaded. If the list is empty,
            all available layers will be loaded
        :param load_mask_layer: If True the mask layer will also be loaded
        :param merge_tiles: If True neighbouring tiles and features will be merged
        :param apply_styles: If True the default styles will be applied
        :param max_tiles: The maximum number of tiles to load
        :param bounds: 
        :param limit_reacher_handler: 
        :return: 
        """
        self.cancel_requested = False
        self.feature_collections_by_layer_path = {}
        self._qgis_layer_groups_by_name = {}
        self._update_progress(show_dialog=True, title="Loading '{}'".format(os.path.basename(self.source.name())))

        min_zoom = self.source.min_zoom()
        max_zoom = self.source.max_zoom()
        if min_zoom is not None and zoom_level < min_zoom:
            zoom_level = min_zoom
        if max_zoom is not None and zoom_level > max_zoom:
            zoom_level = max_zoom

        all_tiles = get_all_tiles(bounds, lambda: self.cancel_requested)
        tiles_to_load = []
        tiles = []
        for t in all_tiles:
            if self.cancel_requested:
                break

            file_name = self._get_tile_cache_name(zoom_level, t[0], t[1])
            tile = FileHelper.get_cached_tile(file_name)
            if tile and tile.decoded_data:
                tiles.append(tile)
            else:
                tiles_to_load.append(t)

        debug("{} cache hits. {} will be loaded from the source.", len(tiles), len(tiles_to_load))

        debug("Loading extent {} for zoom level '{}' of: {}", zoom_level, self.source.name())
        tile_data_tuples = self.source.load_tiles(zoom_level=zoom_level,
                                                  tiles_to_load=tiles_to_load,
                                                  max_tiles=max_tiles,
                                                  for_each=QApplication.processEvents,
                                                  limit_reacher_handler=limit_reacher_handler)
        if len(tiles) == 0 and (not tile_data_tuples or len(tile_data_tuples) == 0):
            QMessageBox.information(None, "No tiles found", "What a pity, no tiles could be found!")

        if load_mask_layer:
            mask_level = self.source.mask_level()
            if mask_level is not None and mask_level != zoom_level:
                debug("Mapping {} tiles to mask level", len(all_tiles))
                scheme = self.source.scheme()
                crs = self.source.crs()
                mask_tiles = map(
                    lambda t: change_zoom(zoom_level, int(mask_level), t, scheme, crs),
                    all_tiles)
                debug("Mapping done")

                mask_tiles_to_load = []
                for t in mask_tiles:
                    file_name = self._get_tile_cache_name(mask_level, t[0], t[1])
                    tile = FileHelper.get_cached_tile(file_name)
                    if tile and tile.decoded_data:
                        tiles.append(tile)
                    else:
                        mask_tiles_to_load.append(t)

                debug("Loading mask layer (zoom_level={})", mask_level)
                mask_layer_data = self.source.load_tiles(zoom_level=mask_level,
                                                         tiles_to_load=mask_tiles_to_load,
                                                         max_tiles=max_tiles,
                                                         for_each=QApplication.processEvents)
                debug("Mask layer loaded")
                tile_data_tuples.extend(mask_layer_data)

        if tile_data_tuples and len(tile_data_tuples) > 0:
            if not self.cancel_requested:
                decoded_tiles = self._decode_tiles(tile_data_tuples)
                tiles.extend(decoded_tiles)
        if len(tiles) > 0:
            if not self.cancel_requested:
                self._process_tiles(tiles, layer_filter)
            if not self.cancel_requested:
                self._create_qgis_layers(merge_features=merge_tiles,
                                         apply_styles=apply_styles)

        self._update_progress(show_dialog=False)
        if self.cancel_requested:
            info("Import cancelled")
        else:
            info("Import complete")

    def _decode_tiles(self, tiles_with_encoded_data):
        """
         * Decodes the PBF data from all the specified tiles and reports the progress
         * If a tile is loaded from the cache, the decoded_data is already set and doesn't have to be encoded
        :param tiles_with_encoded_data:
        :return:
        """
        total_nr_tiles = len(tiles_with_encoded_data)
        info("Decoding {} tiles", total_nr_tiles)
        self._update_progress(progress=0, max_progress=100, msg="Decoding tiles...")

        nr_processors = 4
        try:
            nr_processors = mp.cpu_count()
        except NotImplementedError:
            info("CPU count cannot be retrieved. Falling back to default = 4")

        tiles_with_encoded_data = map(lambda t: (t[0], self._unzip(t[1])), tiles_with_encoded_data)

        pool = mp.Pool(nr_processors)
        tiles = []
        rs = pool.map_async(decode_tile, tiles_with_encoded_data, callback=tiles.extend)
        pool.close()
        current_progress = 0
        while not rs.ready() and not self.cancel_requested:
            QApplication.processEvents()
            remaining = rs._number_left
            index = total_nr_tiles - remaining
            progress = int(100.0 / total_nr_tiles * (index + 1))
            if progress != current_progress:
                current_progress = progress
                self._update_progress(progress=progress)

        for t in tiles:
            cache_file_name = self._get_tile_cache_name(t.zoom_level, t.column, t.row)
            if not os.path.isfile(cache_file_name):
                FileHelper.cache_tile(t, cache_file_name)

        return tiles

    def _unzip(self, data):
        """
         * If the passed data is gzipped, it will be unzipped. Otherwise it will be returned untouched
        :param data:
        :return:
        """

        is_gzipped = FileHelper.is_gzipped(data)
        if is_gzipped:
            file_content = GzipFile('', 'r', 0, StringIO(data)).read()
        else:
            file_content = data
        return file_content

    def _process_tiles(self, tiles, layer_filter):
        """
         * Creates GeoJSON for all the specified tiles and reports the progress
        :param tiles: 
        :return: 
        """
        total_nr_tiles = len(tiles)
        info("Processing {} tiles", total_nr_tiles)
        self._update_progress(progress=0, max_progress=100, msg="Processing features...")
        current_progress = -1
        for index, tile in enumerate(tiles):
            QApplication.processEvents()
            if self.cancel_requested:
                break
            self._create_geojson(tile, layer_filter)
            progress = int(100.0 / total_nr_tiles * (index + 1))
            if progress != current_progress:
                current_progress = progress
                self._update_progress(progress=progress)

    def _get_cartographic_layer_sort_id(self, layer_name):
        """
         * Returns the cartographic sort id for the specified layer.
         * This sort id is the position of the layer in the cartographic_layer_ordering collection.
         * If the layer isn't present in the collection, the sort id wil be 999 and therefore the layer will be added at the bottom.
        :param layer_name: 
        :return: 
        """

        sort_id = 999
        if layer_name in self.cartographic_layer_ordering:
            sort_id = self.cartographic_layer_ordering.index(layer_name)
        return sort_id

    def _assure_qgis_groups_exist(self):
        """
         * Createss a group for each layer that is given by the layer source scheme
         >> mbtiles: value 'JSON' in metadata table, array 'vector_layers'
         >> TileJSON: value 'vector_layers'
        :return: 
        """

        root = QgsProject.instance().layerTreeRoot()
        root_group = root.findGroup(self.source.name())
        if not root_group:
            root_group = root.addGroup(self.source.name())
        layers = map(lambda l: l["id"], self.source.vector_layers())
        layers = sorted(layers, key=lambda x: self._get_cartographic_layer_sort_id(x))
        for index, layer_name in enumerate(layers):
            group = root_group.findGroup(layer_name)
            if not group:
                group = root_group.addGroup(layer_name)
            self._qgis_layer_groups_by_name[layer_name] = group

    def _get_geojson_filename(self, layer_name, geo_type, zoom_level):
        return "{}.{}.{}.{}".format(self.source.name(), layer_name, geo_type, zoom_level)

    def _create_qgis_layers(self, merge_features, apply_styles):
        """
         * Creates a hierarchy of groups and layers in qgis
        """
        debug("Creating hierarchy in QGIS")

        self._assure_qgis_groups_exist()

        self._update_progress(progress=0, max_progress=len(self.feature_collections_by_layer_path), msg="Creating layers...")
        layers = []
        for index, layer_name_and_type in enumerate(self.feature_collections_by_layer_path):
            layer_name_and_zoom = layer_name_and_type[0]
            geo_type = layer_name_and_type[1]
            layer_name = layer_name_and_zoom.split(VtReader._zoom_level_delimiter)[0]
            zoom_level = layer_name_and_zoom.split(VtReader._zoom_level_delimiter)[1]
            QApplication.processEvents()
            if self.cancel_requested:
                break
            target_group = self._qgis_layer_groups_by_name[layer_name]
            feature_collections_by_tile_coord = self.feature_collections_by_layer_path[layer_name_and_type]

            file_name = self._get_geojson_filename(layer_name, geo_type, zoom_level)
            file_path = FileHelper.get_geojson_file_name(file_name)

            layer = None
            if os.path.isfile(file_path):
                # file exists already. add the features of the collection to the existing collection
                # get the layer from qgis and update its source
                layer = self._get_layer_by_source(layer_name_and_zoom, file_path)
                if layer:
                    self._update_layer_source(file_path, feature_collections_by_tile_coord)
                    layer.reload()

            if not layer:
                complete_collection = self._get_empty_feature_collection(zoom_level, layer_name)
                self._merge_feature_collections(current_feature_collection=complete_collection,
                                                feature_collections_by_tile_coord=feature_collections_by_tile_coord)
                with open(file_path, "w") as f:
                    f.write(json.dumps(complete_collection))
                layer = self._add_vector_layer_to_qgis(file_path, layer_name, zoom_level, target_group, merge_features, geo_type)
                if apply_styles:
                    layers.append((layer_name_and_type, layer))
            self._update_progress(progress=index+1)

        if apply_styles:
            self._update_progress(progress=0, max_progress=len(layers), msg="Styling layers...")
            for index, layer_path_tuple in enumerate(layers):
                QApplication.processEvents()
                if self.cancel_requested:
                    break
                path_and_type = layer_path_tuple[0]
                geo_type = path_and_type[1]
                layer = layer_path_tuple[1]
                VtReader._apply_named_style(layer, geo_type)
                self._update_progress(progress=index+1)

    @staticmethod
    def _update_layer_source(layer_source, feature_collections_by_tile_coord):
        """
         * Updates the layers GeoJSON source file
        :param layer_source: 
        :param feature_collections_by_tile_coord: 
        :return: 
        """
        with open(layer_source, "r") as f:
            current_feature_collection = json.load(f)
            VtReader._merge_feature_collections(current_feature_collection, feature_collections_by_tile_coord)
        if current_feature_collection:
            with open(layer_source, "w") as f:
                json.dump(current_feature_collection, f)

    @staticmethod
    def _merge_feature_collections(current_feature_collection, feature_collections_by_tile_coord):
        """
         * Merges the features of multiple tiles into the current_feature_collection if not already present.
        :param current_feature_collection: 
        :param feature_collections_by_tile_coord: 
        :return: 
        """

        for tile_coord in feature_collections_by_tile_coord:
            if tile_coord not in current_feature_collection["tiles"]:
                feature_collection = feature_collections_by_tile_coord[tile_coord]
                current_feature_collection["tiles"].extend(feature_collection["tiles"])
                current_feature_collection["features"].extend(feature_collection["features"])

    @staticmethod
    def _get_layer_by_source(layer_name, layer_source_file):
        """
         * Returns the layer from QGIS whose name and layer_source matches the specified parameters
        :param layer_name: 
        :param layer_source_file: 
        :return: 
        """

        matching_layer = None
        layers = QgsMapLayerRegistry.instance().mapLayersByName(layer_name)
        for l in layers:
            if l.source() == layer_source_file:
                matching_layer = l
                break
        return matching_layer

    @staticmethod
    def _apply_named_style(layer, geo_type):
        """
         * Looks for a styles with the same name as the layer and if one is found, it is applied to the layer
        :param layer: 
        :param layer_path: e.g. 'transportation.service' or 'transportation_name.path'
        :return: 
        """
        try:
            name = layer.name().split(VtReader._zoom_level_delimiter)[0].lower()
            styles = [
                "{}.{}".format(name, geo_type.lower()),
                name
            ]
            for p in styles:
                style_name = "{}.qml".format(p).lower()
                if style_name in VtReader._styles:
                    style_path = os.path.join(FileHelper.get_plugin_directory(), "styles/{}".format(style_name))
                    res = layer.loadNamedStyle(style_path)
                    if res[1]:  # Style loaded
                        layer.setCustomProperty("layerStyle", style_path)
                        if layer.customProperty("layerStyle") == style_path:
                            debug("Style successfully applied: {}", style_name)
                            break
        except:
            critical("Loading style failed: {}", sys.exc_info())

    def _add_vector_layer_to_qgis(self, json_src, layer_name, zoom_level, layer_target_group, merge_features, geo_type):
        """
         * Creates a QgsVectorLayer and adds it to the group specified by layer_target_group
         * Invalid geometries will be removed during the process of merging features over tile boundaries
        """

        layer_with_zoom = "{}{}{}".format(layer_name, VtReader._zoom_level_delimiter, zoom_level)
        layer = QgsVectorLayer(json_src, layer_with_zoom, "ogr")

        if merge_features and geo_type in [GeoTypes.LINE_STRING, GeoTypes.POLYGON]:
            layer = FeatureMerger().merge_features(layer)
            layer.setName(layer_name)

        QgsMapLayerRegistry.instance().addMapLayer(layer, False)
        layer_target_group.addLayer(layer)
        layer.setCustomProperty("vector_tile_source", self.source.source())

        layer.setShortName(layer_name)
        layer.setDataUrl(self.source.source())

        if self.source.name() and "openmaptiles" in self.source.name().lower():
            layer.setDataUrl(remove_key(self.source.source()))
            layer.setAttribution(u"Vector Tiles © Klokan Technologies GmbH (CC-BY), Data © OpenStreetMap contributors (ODbL)")
            layer.setAttributionUrl("https://openmaptiles.com/hosting/")

        return layer

    def _create_geojson(self, tile, layer_filter):
        """
         * Transforms all features of the specified tile into GeoJSON
         * The resulting GeoJSON feature will be applied to the features of the corresponding GeoJSON FeatureCollection
        :param tile:
        :return:
        """
        for layer_name in tile.decoded_data:
            if layer_filter and len(layer_filter) > 0:
                if layer_name not in layer_filter:
                    continue

            tile_features = tile.decoded_data[layer_name]["features"]
            tile_id = tile.id()
            feature_path = "{}{}{}".format(layer_name, VtReader._zoom_level_delimiter, tile.zoom_level)
            for index, feature in enumerate(tile_features):
                if self._is_duplicate_feature(feature, tile):
                    continue

                geojson_feature, geo_type = self._create_geojson_feature(feature, tile)
                if geojson_feature:
                    path_and_type = (feature_path, geo_type)
                    if path_and_type not in self.feature_collections_by_layer_path:
                        self.feature_collections_by_layer_path[path_and_type] = {}
                    collection_dict = self.feature_collections_by_layer_path[path_and_type]
                    if tile_id not in collection_dict:
                        collection_dict[tile_id] = self._get_empty_feature_collection(tile.zoom_level, layer_name)
                    collection = collection_dict[tile_id]

                    collection["features"].append(geojson_feature)
                    if tile_id not in collection["tiles"]:
                        collection["tiles"].append(tile_id)

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

    def _create_geojson_feature(self, feature, tile):
        """
        Creates a GeoJSON feature for the specified feature
        """

        geo_type = VtReader.geo_types[feature["type"]]
        coordinates = feature["geometry"]

        properties = feature["properties"]
        if geo_type == GeoTypes.POINT:
            coordinates = coordinates[0]
            properties["_symbol"] = self._get_poi_icon(feature)
            if not all(0 <= c <= self._extent for c in coordinates):
                return None, None

        coordinates = VtReader._map_coordinates_recursive(
            coordinates=coordinates,
            func=lambda coords: VtReader._get_absolute_coordinates(coords, tile))

        feature_json = VtReader._create_geojson_feature_from_coordinates(geo_type, coordinates, properties)

        return feature_json, geo_type

    def _get_poi_icon(self, feature):
        """
         * Returns the name of the svg icon that will be applied in QGIS.
         * The resulting icon is determined based on class and subclass of the specified feature.
        :param feature: 
        :return: 
        """

        feature_class, feature_subclass = self._get_feature_class_and_subclass(feature)
        root_path = FileHelper.get_icons_directory()
        class_icon = "{}.svg".format(feature_class)
        class_subclass_icon = "{}.{}.svg".format(feature_class, feature_subclass)
        icon_name = "poi.svg"
        if os.path.isfile(os.path.join(root_path, class_subclass_icon)):
            icon_name = class_subclass_icon
        elif os.path.isfile(os.path.join(root_path, class_icon)):
            icon_name = class_icon
        return icon_name

    def _is_duplicate_feature(self, feature, tile):
        """
         * Returns true if the same feature has already been loaded
         * If the feature has not been loaded, it is marked as loaded by calling this function
         * A feature is identified by the tuple: (feature_name, feature_class, feature_subclass)
         * A feature is only loaded if the same feature identifier doesn't occur on the same or a neighbouring tile
        :param feature: 
        :param tile: 
        :return: 
        """
        geo_type = VtReader.geo_types[feature["type"]]
        is_poi = geo_type == GeoTypes.POINT

        is_loaded = False
        if is_poi and VtReader._feature_name(feature):
            feature_id = VtReader._feature_id(feature)
            if feature_id in self._loaded_pois_by_id:
                locations = self._loaded_pois_by_id[feature_id]
                for loc in locations:
                    distance_x = math.fabs(loc["col"] - tile.column)
                    distance_y = math.fabs(loc["row"] - tile.row)
                    distance_threshold = 2
                    is_loaded = distance_x <= distance_threshold and distance_y <= distance_threshold
                    if is_loaded:
                        break
            if not is_loaded:
                if feature_id not in self._loaded_pois_by_id:
                    self._loaded_pois_by_id[feature_id] = []
                self._loaded_pois_by_id[feature_id].append({'col': tile.column, 'row': tile.row})

        return is_loaded

    @staticmethod
    def _feature_id(feature):
        name = VtReader._feature_name(feature)
        feature_class, feature_subclass = VtReader._get_feature_class_and_subclass(feature)
        feature_id = (name, feature_class, feature_subclass)
        return feature_id

    @staticmethod
    def _feature_name(feature):
        """
        * Returns the 'name' property of the feature
        :param feature: 
        :return: 
        """
        name = None
        properties = feature["properties"]
        if "name" in properties:
            name = properties["name"]
        return name

    @staticmethod
    def _is_multi(geo_type, coordinates):
        """
        * Returns true, if the specified coordinates belong to a Multi geometry (e.g. MultiPolygon or MultiLineString)
        :param geo_type: 
        :param coordinates: 
        :return: 
        """

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
        """
        * Returns the depth of an array.
          >> Example: arr=[1,2,3], depth=0, then the resulting depth will be 0
          >> Example: arr=[[1,2], [3,4]], depth=0, then the resulting depth will be 1
        :param arr: 
        :param depth: 
        :return: 
        """

        if all(isinstance(c, numbers.Real) for c in arr[0]):
            return depth
        else:
            depth += 1
            return VtReader.get_array_depth(arr[0], depth)

    @staticmethod
    def _create_geojson_feature_from_coordinates(geo_type, coordinates, properties):
        """
        * Returns a JSON object that represents a GeoJSON feature
        :param geo_type: 
        :param coordinates: 
        :param properties: 
        :return: 
        """

        is_multi = VtReader._is_multi(geo_type, coordinates)

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
        is_coordinate_tuple = len(coordinates) == 2 and all(isinstance(c, int) for c in coordinates)
        if is_coordinate_tuple:
            newval = func(coordinates)
            tmp.append(newval)
        else:
            for coord in coordinates:
                is_coordinate_tuple = len(coord) == 2 and all(isinstance(c, int) for c in coord)
                if is_coordinate_tuple:
                    newval = func(coord)
                    tmp.append(newval)
                else:
                    tmp.append(VtReader._map_coordinates_recursive(coord, func))
        return tmp

    @staticmethod
    def _get_absolute_coordinates(coordinates, tile):
        """
         * The coordinates of a geometry, are relative to the tile the feature is located on.
         * Due to this, we've to get the absolute coordinates of the geometry.
        """

        tile_extent = tile.extent

        delta_x = tile_extent[2] - tile_extent[0]
        delta_y = tile_extent[3] - tile_extent[1]
        merc_easting = int(tile_extent[0] + delta_x / VtReader._extent * coordinates[0])
        merc_northing = int(tile_extent[1] + delta_y / VtReader._extent * coordinates[1])
        return [merc_easting, merc_northing]

    def enable_cartographic_ordering(self, enabled):
        self.cartographic_ordering_enabled = enabled
