#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import json
import math

from log_helper import info, warn, critical, debug, remove_key
from PyQt4.QtGui import QApplication
from tile_helper import get_all_tiles, change_zoom, get_code_from_epsg
from feature_helper import FeatureMerger, is_multi, map_coordinates_recursive, GeoTypes, geo_types
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


class VtReader:

    omt_layer_ordering = [
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

    _layers_to_dissolve = []
    _zoom_level_delimiter = "*"
    _DEFAULT_EXTENT = 4096

    _styles = FileHelper.get_styles()

    flush_layers_of_other_zoom_level = False

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
        self.progress_handler = progress_handler
        self.feature_collections_by_layer_path = {}
        self._qgis_layer_groups_by_name = {}
        self.cancel_requested = False
        self._loaded_pois_by_id = {}
        self._clip_tiles_at_tile_bounds = None
        self._always_overwrite_geojson = False
        self._root_group_name = None
        self._flush = False

    def set_root_group_name(self, name):
        self._root_group_name = name

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
            "scheme": self.source.scheme(),
            "layer": layer_name,
            "zoom_level": zoom_level,
            "type": "FeatureCollection",
            "crs": crs,
            "features": []}

    def always_overwrite_geojson(self, enabled):
        """
         * If activated, the geoJson written to the disk will always be overwritten, with each load
         * As a result of this, only the latest loaded extent will be visible in qgis
        :return:
        """
        self._always_overwrite_geojson = enabled

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

    def load_tiles(self, zoom_level, layer_filter, load_mask_layer=False, merge_tiles=True, clip_tiles=False,
                   apply_styles=True, max_tiles=None, bounds=None, limit_reacher_handler=None):
        """
         * Loads the vector tiles from either a file or a URL and adds them to QGIS
        :param clip_tiles: 
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
        self._clip_tiles_at_tile_bounds = clip_tiles

        min_zoom = self.source.min_zoom()
        max_zoom = self.source.max_zoom()
        if min_zoom is not None and zoom_level < min_zoom:
            zoom_level = min_zoom
        if max_zoom is not None and zoom_level > max_zoom:
            zoom_level = max_zoom

        all_tiles = get_all_tiles(
            bounds=bounds,
            is_cancel_requested_handler=lambda: self.cancel_requested,
            for_each=lambda: QApplication.processEvents())
        tiles_to_load = set()
        tiles = []
        tiles_to_ignore = set()
        for t in all_tiles:
            if self.cancel_requested or (max_tiles and len(tiles) >= max_tiles):
                break

            file_name = self._get_tile_cache_name(zoom_level, t[0], t[1])
            tile = FileHelper.get_cached_tile(file_name)
            if tile and tile.decoded_data:
                tiles.append(tile)
                tiles_to_ignore.add((tile.column, tile.row))
            else:
                tiles_to_load.add(t)

        remaining_nr_of_tiles = len(tiles_to_load)
        if max_tiles:
            if len(tiles) + len(tiles_to_load) >= max_tiles:
                remaining_nr_of_tiles = max_tiles - len(tiles)
                if remaining_nr_of_tiles < 0:
                    remaining_nr_of_tiles = 0
        debug("{} cache hits. {} may potentially be loaded.", len(tiles), remaining_nr_of_tiles)

        debug("Loading data for zoom level '{}' source '{}'", zoom_level, self.source.name())

        tile_data_tuples = []
        if remaining_nr_of_tiles > 0:
            tile_data_tuples = self.source.load_tiles(zoom_level=zoom_level,
                                                      tiles_to_load=tiles_to_load,
                                                      max_tiles=remaining_nr_of_tiles,
                                                      for_each=QApplication.processEvents,
                                                      limit_reacher_handler=limit_reacher_handler)
        if len(tiles) == 0 and (not tile_data_tuples or len(tile_data_tuples) == 0):
            QMessageBox.information(None, "No tiles found", "What a pity, no tiles could be found!")

        if load_mask_layer:
            mask_level = self.source.mask_level()
            if mask_level is not None and mask_level != zoom_level:
                debug("Mapping {} tiles to mask level", len(all_tiles))
                scheme = self.source.scheme()
                mask_tiles = map(
                    lambda t: change_zoom(zoom_level, int(mask_level), t, scheme),
                    all_tiles)
                debug("Mapping done")

                mask_tiles_to_load = set()
                for t in mask_tiles:
                    file_name = self._get_tile_cache_name(mask_level, t[0], t[1])
                    tile = FileHelper.get_cached_tile(file_name)
                    if tile and tile.decoded_data:
                        tiles.append(tile)
                    else:
                        mask_tiles_to_load.add(t)

                debug("Loading mask layer (zoom_level={})", mask_level)
                tile_data_tuples = []
                if len(mask_tiles_to_load) > 0:
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
        loaded_tiles_x = map(lambda t: t.coord()[0], tiles)
        loaded_tiles_y = map(lambda t: t.coord()[1], tiles)
        if len(loaded_tiles_x) == 0 or len(loaded_tiles_y) == 0:
            return None

        loaded_extent = {"x_min": min(loaded_tiles_x),
                         "x_max": max(loaded_tiles_x),
                         "y_min": min(loaded_tiles_y),
                         "y_max": max(loaded_tiles_y)}
        loaded_extent["width"] = loaded_extent["x_max"] - loaded_extent["x_min"] + 1
        loaded_extent["height"] = loaded_extent["y_max"] - loaded_extent["y_min"] + 1

        return loaded_extent

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

        tiles = filter(lambda ti: ti.decoded_data is not None, tiles)

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

    def _get_omt_layer_sort_id(self, layer_name):
        """
         * Returns the cartographic sort id for the specified layer.
         * This sort id is the position of the layer in the omt_layer_ordering collection.
         * If the layer isn't present in the collection, the sort id wil be 999 and therefore the layer will be added at the bottom.
        :param layer_name: 
        :return: 
        """

        sort_id = 999
        if layer_name in self.omt_layer_ordering:
            sort_id = self.omt_layer_ordering.index(layer_name)
        return sort_id

    def _assure_qgis_groups_exist(self, manual_layer_name=None, sort_layers=False):
        """
         * Createss a group for each layer that is given by the layer source scheme
         >> mbtiles: value 'JSON' in metadata table, array 'vector_layers'
         >> TileJSON: value 'vector_layers'
        :return: 
        """

        root = QgsProject.instance().layerTreeRoot()
        name = self._root_group_name
        if not name:
            name = self.source.name()
        root_group = root.findGroup(name)
        if not root_group:
            root_group = root.addGroup(name)
        if not manual_layer_name:
            layers = map(lambda l: l["id"], self.source.vector_layers())
        else:
            layers = [manual_layer_name]

        if sort_layers:
            layers = sorted(layers, key=lambda x: self._get_omt_layer_sort_id(x))
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

        self._assure_qgis_groups_exist(sort_layers=apply_styles)

        qgis_layers = QgsMapLayerRegistry.instance().mapLayers().iteritems()
        vt_qgis_name_layer_tuples = filter(lambda (n, l): l.customProperty("vector_tile_source") is not None, qgis_layers)
        own_layers = map(lambda (n, l): l, vt_qgis_name_layer_tuples)

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

            self._assure_qgis_groups_exist(manual_layer_name=layer_name, sort_layers=apply_styles)
            feature_collections_by_tile_coord = self.feature_collections_by_layer_path[layer_name_and_type]

            file_name = self._get_geojson_filename(layer_name, geo_type, zoom_level)
            file_path = FileHelper.get_geojson_file_name(file_name)

            layer = None
            if os.path.isfile(file_path):
                # file exists already. add the features of the collection to the existing collection
                # get the layer from qgis and update its source
                layer = self._get_layer_by_source(own_layers, layer_name_and_zoom, file_path, geo_type)
                if layer:
                    self._update_layer_source(file_path, feature_collections_by_tile_coord, zoom_level, layer_name)

            if not layer:
                complete_collection = self._get_empty_feature_collection(zoom_level, layer_name)
                self._merge_feature_collections(current_feature_collection=complete_collection,
                                                feature_collections_by_tile_coord=feature_collections_by_tile_coord)
                with open(file_path, "w") as f:
                    f.write(json.dumps(complete_collection))
                layer = self._create_named_layer(file_path, layer_name, zoom_level, merge_features, geo_type)
                layers.append((layer_name, geo_type, layer))
            self._update_progress(progress=index+1)

        if self.flush_layers_of_other_zoom_level:
            layers_to_remove = filter(lambda l: l.name().split(self._zoom_level_delimiter)[1] != zoom_level, own_layers)
            ids = map(lambda l: l.id(), layers_to_remove)
            debug("Flushing layers: {}", ids)
            QgsMapLayerRegistry.instance().removeMapLayers(ids)

        QgsMapLayerRegistry.instance().reloadAllLayers()

        if len(layers) > 0:
            only_layers = list(map(lambda layer_name_tuple: layer_name_tuple[2], layers))
            QgsMapLayerRegistry.instance().addMapLayers(only_layers, False)
        for name, geo_type, layer in layers:
            target_group = self._qgis_layer_groups_by_name[name]
            target_group.addLayer(layer)

        if apply_styles:
            self._update_progress(progress=0, max_progress=len(layers), msg="Styling layers...")
            for index, layer_path_tuple in enumerate(layers):
                QApplication.processEvents()
                if self.cancel_requested:
                    break
                geo_type = layer_path_tuple[1]
                layer = layer_path_tuple[2]
                VtReader._apply_named_style(layer, geo_type)
                self._update_progress(progress=index+1)

    def _update_layer_source(self, layer_source, feature_collections_by_tile_coord, zoom_level, layer_name):
        """
         * Updates the layers GeoJSON source file
        :param layer_source: 
        :param feature_collections_by_tile_coord: 
        :return: 
        """
        if self._always_overwrite_geojson:
            current_feature_collection = self._get_empty_feature_collection(zoom_level, layer_name)
        else:
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
    def _get_layer_by_source(all_layers, layer_name, layer_source_file, geo_type):
        """
         * Returns the layer from QGIS whose name and layer_source matches the specified parameters
        :param layer_name: 
        :param layer_source_file: 
        :return: 
        """
        layers = filter(lambda l: l.name() == layer_name and l.source() == layer_source_file, all_layers)
        if len(layers) > 0:
            return layers[0]
        return None

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

    def _create_named_layer(self, json_src, layer_name, zoom_level, merge_features, geo_type):
        """
         * Creates a QgsVectorLayer and adds it to the group specified by layer_target_group
         * Invalid geometries will be removed during the process of merging features over tile boundaries
        """

        layer_with_zoom = "{}{}{}".format(layer_name, VtReader._zoom_level_delimiter, zoom_level)
        layer = QgsVectorLayer(json_src, layer_with_zoom, "ogr")

        layer.setCustomProperty("vector_tile_source", self.source.source())
        layer.setShortName(layer_name)
        layer.setDataUrl(self.source.source())

        if self.source.name() and "openmaptiles" in self.source.name().lower():
            layer.setDataUrl(remove_key(self.source.source()))
            layer.setAttribution(u"Vector Tiles © Klokan Technologies GmbH (CC-BY), Data © OpenStreetMap contributors (ODbL)")
            layer.setAttributionUrl("https://openmaptiles.com/hosting/")

        if merge_features and geo_type in [GeoTypes.LINE_STRING, GeoTypes.POLYGON]:
            layer = FeatureMerger().merge_features(layer)
            layer.setName(layer_name)
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

            layer = tile.decoded_data[layer_name]
            if "extent" in layer:
                extent = layer["extent"]
            else:
                extent = self._DEFAULT_EXTENT
            tile_features = layer["features"]
            tile_id = tile.id()
            feature_path = "{}{}{}".format(layer_name, VtReader._zoom_level_delimiter, tile.zoom_level)
            for index, feature in enumerate(tile_features):
                if self._is_duplicate_feature(feature, tile) or self.cancel_requested:
                    continue

                geojson_feature, geo_type = self._create_geojson_feature(feature, tile, extent)
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

    def _create_geojson_feature(self, feature, tile, current_layer_tile_extent):
        """
        Creates a GeoJSON feature for the specified feature
        """

        geo_type = geo_types[feature["type"]]
        coordinates = feature["geometry"]

        properties = feature["properties"]
        properties["_col"] = tile.column
        properties["_row"] = tile.row
        if "id" in properties and properties["id"] < 0:
            properties["id"] = 0

        if geo_type == GeoTypes.POINT:
            coordinates = coordinates[0]
            properties["_symbol"] = self._get_poi_icon(feature)
            if self._clip_tiles_at_tile_bounds and not all(0 <= c <= current_layer_tile_extent for c in coordinates):
                return None, None
        all_out_of_bounds = []
        coordinates = map_coordinates_recursive(coordinates=coordinates,
                                                tile_extent=current_layer_tile_extent,
                                                mapper_func=lambda coords: VtReader._get_absolute_coordinates(coords,
                                                                                                              tile,
                                                                                                              current_layer_tile_extent),
                                                all_out_of_bounds_func=lambda out_of_bounds: all_out_of_bounds.append(
                                                    out_of_bounds))

        if self._clip_tiles_at_tile_bounds and all(c is True for c in all_out_of_bounds):
            return None, None

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
        geo_type = geo_types[feature["type"]]
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
    def _create_geojson_feature_from_coordinates(geo_type, coordinates, properties):
        """
        * Returns a JSON object that represents a GeoJSON feature
        :param geo_type: 
        :param coordinates: 
        :param properties: 
        :return: 
        """
        type_string = geo_type
        if is_multi(geo_type, coordinates):
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
    def _get_absolute_coordinates(coordinates, tile, extent):
        """
         * The coordinates of a geometry, are relative to the tile the feature is located on.
         * Due to this, we've to get the absolute coordinates of the geometry.
        """
        delta_x = tile.extent[2] - tile.extent[0]
        delta_y = tile.extent[3] - tile.extent[1]
        merc_easting = int(tile.extent[0] + delta_x / extent * coordinates[0])
        merc_northing = int(tile.extent[1] + delta_y / extent * coordinates[1])
        return [merc_easting, merc_northing]
