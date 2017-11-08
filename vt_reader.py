#!/usr/bin/env python
# -*- coding: utf-8 -*-

from future import standard_library
standard_library.install_aliases()
from builtins import map
from builtins import filter
from builtins import str
from itertools import *
import sys
import os
import json
import uuid
import traceback

from log_helper import info, critical, debug, remove_key
from tile_helper import get_all_tiles, get_code_from_epsg, clamp, create_bounds
from feature_helper import (FeatureMerger,
                            geo_types_by_name,
                            geo_types,
                            is_multi,
                            map_coordinates_recursive,
                            GeoTypes,
                            clip_features)
from file_helper import (get_cached_tile_file_name,
                         get_styles,
                         assure_temp_dirs_exist,
                         get_cached_tile, is_gzipped,
                         get_geojson_file_name,
                         get_plugin_directory,
                         get_icons_directory,
                         cache_tile)
from qgis.core import QgsVectorLayer, QgsProject, QgsMapLayerRegistry, QgsExpressionContextUtils
from PyQt4.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from PyQt4.QtGui import QApplication
from io import BytesIO
from gzip import GzipFile
from tile_source import ServerSource, MBTilesSource, TrexCacheSource
from connection import ConnectionTypes

from mp_helper import decode_tile_native, decode_tile_python, can_load_lib

import multiprocessing as mp

is_windows = sys.platform.startswith("win32")

if is_windows:
    # OSGeo4W does not bundle python in exec_prefix for python
    path = os.path.abspath(os.path.join(sys.exec_prefix, '../../bin/pythonw.exe'))
    mp.set_executable(path)
    sys.argv = [None]


class VtReader(QObject):

    progress_changed = pyqtSignal(int, name='progressChanged')
    max_progress_changed = pyqtSignal(int, name='maxProgressChanged')
    message_changed = pyqtSignal('QString', name='messageChanged')
    show_progress_changed = pyqtSignal(bool, name='show_progress_changed')
    loading_finished = pyqtSignal(int, dict, name='loadingFinished')
    tile_limit_reached = pyqtSignal(int, name='tile_limit_reached')
    cancelled = pyqtSignal(name='cancelled')
    add_layer_to_group = pyqtSignal(object, name='add_layer_to_group')

    _loading_options = {
            'zoom_level': None,
            'layer_filter': None,
            'load_mask_layer': None,
            'merge_tiles': None,
            'clip_tiles': None,
            'apply_styles': None,
            'max_tiles': None,
            'bounds': None
        }

    _layers_to_dissolve = []
    _zoom_level_delimiter = "*"
    _DEFAULT_EXTENT = 4096
    _id = str(uuid.uuid4())

    _styles = get_styles()

    flush_layers_of_other_zoom_level = False

    _all_tiles = []

    def __init__(self, iface, connectionn):
        """
         * The mbtiles_path can also be an URL in zxy format: z=zoom, x=tile column, y=tile row
        :param iface: 
        :param path_or_url: 
        """
        QObject.__init__(self)
        if not connectionn:
            raise RuntimeError("The datasource is required")

        self._connection = connectionn
        self._source = self._create_source(connectionn)
        self._external_source = self._create_source(connectionn)

        assure_temp_dirs_exist()
        self.iface = iface
        self.feature_collections_by_layer_name_and_geotype = {}
        self.cancel_requested = False
        self._loaded_pois_by_id = {}
        self._clip_tiles_at_tile_bounds = None
        self._always_overwrite_geojson = False
        self._flush = False
        self._feature_count = None

    def connection(self):
        return self._connection

    def get_source(self):
        """
         * Returns the source being used of the current reader. This method is intended for external use,
         i.e. from outside of this reader. SQlite objects must only be used in the thread they were created.
         As a result of this, each reader creates two identical connections, but one is created within and one
         outisde of the thread.
        :return:
        """

        return self._external_source

    def _create_source(self, connection):
        conn_type = connection["type"]
        if conn_type == ConnectionTypes.TileJSON:
            source = ServerSource(url=connection["url"])
        elif conn_type == ConnectionTypes.MBTiles:
            source = MBTilesSource(path=connection["path"])
        elif conn_type == ConnectionTypes.Trex:
            source = TrexCacheSource(path=connection["path"])
        else:
            raise RuntimeError("Type not set on connection")
        source.progress_changed.connect(self._source_progress_changed)
        source.max_progress_changed.connect(self._source_max_progress_changed)
        source.message_changed.connect(self._source_message_changed)
        source.tile_limit_reached.connect(self._source_tile_limit_reached)
        return source

    def shutdown(self):
        info("Shutdown reader")
        self._source.progress_changed.disconnect()
        self._source.max_progress_changed.disconnect()
        self._source.message_changed.disconnect()
        self._source.close_connection()

    def id(self):
        return self._id

    @pyqtSlot(int)
    def _source_tile_limit_reached(self):
        self.tile_limit_reached.emit(self._loading_options["max_tiles"])

    @pyqtSlot(int)
    def _source_progress_changed(self, progress):
        self._update_progress(progress=progress)

    @pyqtSlot(int)
    def _source_max_progress_changed(self, max_progress):
        self._update_progress(max_progress=max_progress)

    @pyqtSlot('QString')
    def _source_message_changed(self, msg):
        self._update_progress(msg=msg)

    def _update_progress(self, show_dialog=None, progress=None, max_progress=None, msg=None):
        if progress is not None:
            self.progress_changed.emit(progress)
        if max_progress is not None:
            self.max_progress_changed.emit(max_progress)
        if msg:
            self.message_changed.emit(msg)
        if show_dialog:
            self.show_progress_changed.emit(show_dialog)

    def _get_empty_feature_collection(self, layer_name, zoom_level):
        """
         * Returns an empty GeoJSON FeatureCollection with the coordinate reference system (crs) set to EPSG3857
        """
        # todo: when improving CRS handling: the correct CRS of the source has to be set here

        source_crs = self._source.crs()
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
            "source": self._source.name(),
            "scheme": self._source.scheme(),
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
        if self._source:
            self._source.cancel()

    def _get_clamped_zoom_level(self):
        zoom_level = self._loading_options["zoom_level"]
        min_zoom = self._source.min_zoom()
        max_zoom = self._source.max_zoom()
        zoom_level = clamp(zoom_level, low=min_zoom, high=max_zoom)
        return zoom_level

    def _load_tiles(self):
        # recreate source to assure the source belongs to the new thread, SQLite3 isn't happy about it otherwise
        self._source = self._create_source(self.connection())

        try:
            if can_load_lib():
                info("Native decoding supported!!!")
            else:
                bits = "32"
                if sys.maxsize > 2**32:
                    bits = "64"
                info("Native decoding not supported: {}, {}bit", sys.platform, bits)

            self._feature_count = 0
            self._all_tiles = []

            bounds = self._loading_options["bounds"]
            clip_tiles = self._loading_options["clip_tiles"]
            max_tiles = self._loading_options["max_tiles"]
            layer_filter = self._loading_options["layer_filter"]
            info("Tile limit enabled: {}", max_tiles is not None and max_tiles > 0)
            self.cancel_requested = False
            self.feature_collections_by_layer_name_and_geotype = {}
            self._update_progress(show_dialog=True)
            self._clip_tiles_at_tile_bounds = clip_tiles

            zoom_level = self._get_clamped_zoom_level()

            all_tiles = get_all_tiles(
                bounds=bounds,
                is_cancel_requested_handler=lambda: self.cancel_requested,
            )
            tiles_to_load = set()
            cached_tiles = []
            tiles_to_ignore = set()
            for t in all_tiles:
                if self.cancel_requested or (max_tiles and len(cached_tiles) >= max_tiles):
                    break

                file_name = get_cached_tile_file_name(self._source.name(), zoom_level, t[0], t[1])
                tile = get_cached_tile(file_name)
                if tile and tile.decoded_data:
                    cached_tiles.append(tile)
                    tiles_to_ignore.add((tile.column, tile.row))
                else:
                    tiles_to_load.add(t)

            remaining_nr_of_tiles = len(tiles_to_load)
            if max_tiles:
                if len(cached_tiles) + len(tiles_to_load) >= max_tiles:
                    remaining_nr_of_tiles = max_tiles - len(cached_tiles)
                    if remaining_nr_of_tiles < 0:
                        remaining_nr_of_tiles = 0
            if len(cached_tiles) > 0:
                info("{} tiles in cache. Max. {} will be loaded additionally.", len(cached_tiles), remaining_nr_of_tiles)
                if not self.cancel_requested:
                    self._process_tiles(cached_tiles, layer_filter)
                    self._all_tiles.extend(cached_tiles)

            debug("Loading data for zoom level '{}' source '{}'", zoom_level, self._source.name())

            if remaining_nr_of_tiles > 0:
                tile_data_tuples = self._source.load_tiles(zoom_level=zoom_level,
                                                          tiles_to_load=tiles_to_load,
                                                          max_tiles=remaining_nr_of_tiles)
                if len(tile_data_tuples) > 0 and not self.cancel_requested:
                    tiles = self._decode_tiles(tile_data_tuples)
                    self._process_tiles(tiles, layer_filter)
                    for t in tiles:
                        cache_tile(t, self._source.name())
                    self._all_tiles.extend(tiles)
            self._continue_loading()

        except Exception as e:
            tb = ""
            if traceback:
                tb = traceback.format_exc()
            critical("An exception occured: {}, {}", e, tb)
            self.cancelled.emit()

    def _continue_loading(self):
        zoom_level = self._loading_options["zoom_level"]
        merge_tiles = self._loading_options["merge_tiles"]
        apply_styles = self._loading_options["apply_styles"]
        clip_tiles = self._loading_options["clip_tiles"]
        if not self.cancel_requested:
            self._create_qgis_layers(merge_features=merge_tiles,
                                     apply_styles=apply_styles,
                                     clip_tiles=clip_tiles)

        self._update_progress(show_dialog=False)
        if self.cancel_requested:
            info("Import cancelled")
            self.cancelled.emit()
        else:
            info("Import complete")
            loaded_extent = self._get_extent(self._all_tiles, zoom_level)
            self.loading_finished.emit(zoom_level, loaded_extent)

    @staticmethod
    def _get_extent(tiles, zoom_level):
        loaded_tiles_x = [t.coord()[0] for t in tiles]
        loaded_tiles_y = [t.coord()[1] for t in tiles]
        if len(loaded_tiles_x) == 0 or len(loaded_tiles_y) == 0:
            return None

        bounds = create_bounds(zoom=zoom_level,
                               x_min=min(loaded_tiles_x),
                               x_max=max(loaded_tiles_x),
                               y_min=min(loaded_tiles_y),
                               y_max=max(loaded_tiles_y))
        return bounds

    def set_options(self, load_mask_layer=False, merge_tiles=True, clip_tiles=False,
                    apply_styles=True, max_tiles=None, layer_filter=None):
        """
         * Specify the reader options
        :param load_mask_layer:  If True the mask layer will also be loaded
        :param merge_tiles: If True neighbouring tiles and features will be merged
        :param clip_tiles: If True the features located outside the tile will be removed
        :param apply_styles: If True the default styles will be applied
        :param max_tiles: The maximum number of tiles to load
        :param layer_filter: A list of layers. If any layers are set, only these will be loaded. If the list is empty,
            all available layers will be loaded
        :return:
        """
        self._loading_options = {
            'load_mask_layer': load_mask_layer,
            'merge_tiles': merge_tiles,
            'clip_tiles': clip_tiles,
            'apply_styles': apply_styles,
            'max_tiles': max_tiles,
            'layer_filter': layer_filter
        }

    def load_tiles_async(self, zoom_level, bounds):
        """
         * Loads the vector tiles from either a file or a URL and adds them to QGIS
        :param zoom_level: The zoom level to load
        :param bounds:
        :return: 
        """
        self._loading_options["zoom_level"] = zoom_level
        self._loading_options["bounds"] = bounds
        _worker_thread = QThread(self.iface.mainWindow())
        self.moveToThread(_worker_thread)
        _worker_thread.started.connect(self._load_tiles)
        _worker_thread.start()

    @staticmethod
    def _get_pool(cores=None):
        nr_processors = 4
        if cores:
            nr_processors = cores
        try:
            nr_processors = mp.cpu_count()
        except NotImplementedError:
            info("CPU count cannot be retrieved. Falling back to default = 4")
        pool = mp.Pool(nr_processors)
        return pool

    def _decode_tiles(self, tiles_with_encoded_data):
        """
         * Decodes the PBF data from all the specified tiles and reports the progress
         * If a tile is loaded from the cache, the decoded_data is already set and doesn't have to be encoded
        :param tiles_with_encoded_data:
        :return:
        """

        tiles_with_encoded_data = [(t[0], self._unzip(t[1])) for t in tiles_with_encoded_data]

        if can_load_lib():
            decoder_func = decode_tile_native
        else:
            decoder_func = decode_tile_python

        tiles = []

        tile_data_tuples = []

        if len(tiles_with_encoded_data) < 30:
            for t in tiles_with_encoded_data:
                tile, decoded_data = decoder_func(t)
                if decoded_data:
                    tile_data_tuples.append((tile, decoded_data))
        else:
            pool = self._get_pool()
            rs = pool.map_async(decoder_func, tiles_with_encoded_data, callback=tile_data_tuples.extend)
            pool.close()
            current_progress = 0
            nr_of_tiles = len(tiles_with_encoded_data)
            self._update_progress(max_progress=nr_of_tiles, msg="Decoding {} tiles...".format(nr_of_tiles))
            while not rs.ready() and not self.cancel_requested:
                if self.cancel_requested:
                    pool.terminate()
                    break
                else:
                    QApplication.processEvents()
                    remaining = rs._number_left
                    index = nr_of_tiles - remaining
                    progress = int(100.0 / nr_of_tiles * (index + 1))
                    if progress != current_progress:
                        current_progress = progress
                        self._update_progress(progress=progress)

        tile_data_tuples = sorted(tile_data_tuples, key=lambda t: t[0].id())
        groups = groupby(tile_data_tuples, lambda t: t[0].id())
        for key, group in groups:
            tile = None
            data = {}
            for t, decoded_data in list(group):
                if not decoded_data:
                    continue

                if not tile:
                    tile = t
                for layer_name in decoded_data:
                    data[layer_name] = decoded_data[layer_name]
            tile.decoded_data = data
            tiles.append(tile)

        info("Decoding finished, {} tiles with data", len(tiles))
        return tiles

    @staticmethod
    def _get_feature_count(tiles):
        total_nr_of_features = 0
        for tile in tiles:
            for layer_name in tile.decoded_data:
                layer = tile.decoded_data[layer_name]
                total_nr_of_features += len(layer["features"])
        return total_nr_of_features

    @staticmethod
    def _unzip(data):
        """
         * If the passed data is gzipped, it will be unzipped. Otherwise it will be returned untouched
        :param data:
        :return:
        """

        is_zipped = is_gzipped(data)
        if is_zipped:
            file_content = GzipFile('', 'r', 0, BytesIO(data)).read()
        else:
            file_content = data
        return file_content

    def _process_tile(self, tile, layer_filter):
        self._add_features_to_feature_collection(tile, layer_filter)

    def _process_tiles(self, tiles, layer_filter):
        """
         * Creates GeoJSON for all the specified tiles and reports the progress
        :param tiles: 
        :return: 
        """
        nr_of_features = self._get_feature_count(tiles)
        self._update_progress(msg="Processing {} features of {} tiles...".format(nr_of_features, len(tiles)),
                              max_progress=len(tiles))
        for index, tile in enumerate(tiles):
            if self.cancel_requested:
                break
            if tile.decoded_data:
                self._all_tiles.append(tile)
                self._add_features_to_feature_collection(tile, layer_filter=layer_filter)
            self._update_progress(progress=index+1)

    def _get_geojson_filename(self, layer_name, geo_type):
        return "{}.{}.{}".format(self._source.name().replace(" ", "_"), layer_name, geo_type)

    def _create_qgis_layers(self, merge_features, apply_styles, clip_tiles):
        """
         * Creates a hierarchy of groups and layers in qgis
        """
        debug("Creating hierarchy in QGIS")

        # self._assure_qgis_groups_exist(sort_layers=apply_styles)

        qgis_layers = QgsMapLayerRegistry.instance().mapLayers()
        vt_qgis_name_layer_tuples = list(filter(lambda (n, l): l.customProperty("vector_tile_source") == self._source.source(), iter(qgis_layers.items())))
        own_layers = list(map(lambda (n, l): l, vt_qgis_name_layer_tuples))
        for l in own_layers:
            name = l.name()
            geo_type = l.customProperty("geo_type")
            if (name, geo_type) not in self.feature_collections_by_layer_name_and_geotype:
                self._update_layer_source(l.source(), self._get_empty_feature_collection(0, l.name()))

        self._update_progress(progress=0,
                              max_progress=len(self.feature_collections_by_layer_name_and_geotype),
                              msg="Creating layers...")
        new_layers = []
        count = 0
        for layer_name, geo_type in self.feature_collections_by_layer_name_and_geotype:
            count += 1
            if self.cancel_requested:
                break

            feature_collection = self.feature_collections_by_layer_name_and_geotype[(layer_name, geo_type)]
            zoom_level = feature_collection["zoom_level"]

            file_name = self._get_geojson_filename(layer_name, geo_type)
            file_path = get_geojson_file_name(file_name)

            layer = None
            if os.path.isfile(file_path):
                # file exists already. add the features of the collection to the existing collection
                # get the layer from qgis and update its source
                layer = self._get_layer_by_source(own_layers, layer_name, file_path)
                if layer:
                    self._update_layer_source(file_path, feature_collection)
                    if merge_features and geo_type in [GeoTypes.LINE_STRING, GeoTypes.POLYGON]:
                        FeatureMerger().merge_features(layer)
                    if clip_tiles:
                        clip_features(layer=layer, scheme=self._source.scheme())

            if not layer:
                self._update_layer_source(file_path, feature_collection)
                layer = self._create_named_layer(file_path, layer_name, zoom_level)
                if merge_features and geo_type in [GeoTypes.LINE_STRING, GeoTypes.POLYGON]:
                    FeatureMerger().merge_features(layer)
                if clip_tiles:
                    clip_features(layer=layer, scheme=self._source.scheme())
                new_layers.append((layer_name, geo_type, layer))
            self._update_progress(progress=count+1)

        self._update_progress(msg="Refresh layers...")
        QgsMapLayerRegistry.instance().reloadAllLayers()

        if len(new_layers) > 0:
            self._update_progress(msg="Adding new layers...")
            only_layers = list([layer_name_tuple[2] for layer_name_tuple in new_layers])
            QgsMapLayerRegistry.instance().addMapLayers(only_layers, False)
        for name, geo_type, layer in new_layers:
            self.add_layer_to_group.emit(layer)

        if apply_styles:
            count = 0
            self._update_progress(progress=0, max_progress=len(new_layers), msg="Styling layers...")
            for name, geo_type, layer in new_layers:
                count += 1
                if self.cancel_requested:
                    break
                VtReader._apply_named_style(layer, geo_type)
                self._update_progress(progress=count)

    @staticmethod
    def _update_layer_source(layer_source, feature_collection):
        """
         * Updates the layers GeoJSON source file
        :param layer_source: The path to the geoJSON file that is the source of the layer
        :param feature_collection: The feature collection to dump
        :return: 
        """
        with open(layer_source, "w") as f:
            f.write(json.dumps(feature_collection))

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
    def _get_layer_by_source(all_layers, layer_name, layer_source_file):
        """
         * Returns the layer from QGIS whose name and layer_source matches the specified parameters
        :param layer_name: 
        :param layer_source_file: 
        :return: 
        """
        layers = [l for l in all_layers if l.name() == layer_name and l.source() == layer_source_file]
        if len(layers) > 0:
            return layers[0]
        return None

    @staticmethod
    def _apply_named_style(layer, geo_type):
        """
         * Looks for a styles with the same name as the layer and if one is found, it is applied to the layer
        :param layer: The layer to which the style shall be applied
        :param geo_type: The geo type of the features on the layer (point, linestring or polygon)
        :return: 
        """
        try:
            name = layer.name().lower()
            styles = [
                "{}.{}".format(name, geo_type.lower()),
                name
            ]
            for p in styles:
                style_name = "{}.qml".format(p).lower()
                if style_name in VtReader._styles:
                    style_path = os.path.join(get_plugin_directory(), "styles/{}".format(style_name))
                    res = layer.loadNamedStyle(style_path)
                    if res[1]:  # Style loaded
                        layer.setCustomProperty("layerStyle", style_path)
                        if layer.customProperty("layerStyle") == style_path:
                            debug("Style successfully applied: {}", style_name)
                            break
        except:
            critical("Loading style failed: {}", sys.exc_info())

    def _create_named_layer(self, json_src, layer_name, zoom_level):
        """
         * Creates a QgsVectorLayer and adds it to the group specified by layer_target_group
         * Invalid geometries will be removed during the process of merging features over tile boundaries
        """

        source_url = self._source.source()
        layer = QgsVectorLayer(json_src, layer_name, "ogr")

        layer.setCustomProperty("vector_tile_source", source_url)
        layer.setCustomProperty("zoom_level", zoom_level)
        layer.setShortName(layer_name)
        layer.setDataUrl(source_url)

        layer.setDataUrl(remove_key(source_url))
        if self._source.name() and "openmaptiles" in self._source.name().lower():
            layer.setAttribution(u"Vector Tiles © Klokan Technologies GmbH (CC-BY), Data © OpenStreetMap contributors "
                                 u"(ODbL)")
            layer.setAttributionUrl("https://openmaptiles.com/hosting/")
        return layer

    def _handle_geojson_features(self, tile, layer_name, features):
        tile_id = tile.id()
        for geojson_feature in features:
            geo_type = None
            geom_type = str(geojson_feature["geometry"]["type"])
            if geom_type.endswith("Polygon"):
                geo_type = GeoTypes.POLYGON
            elif geom_type.endswith("Point"):
                geo_type = GeoTypes.POINT
            elif geom_type.endswith("LineString"):
                geo_type = GeoTypes.LINE_STRING
            assert geo_type is not None

            feature_collection = self._get_feature_collection(layer_name=layer_name,
                                                              geo_type=geo_type,
                                                              zoom_level=tile.zoom_level)

            feature_collection["features"].append(geojson_feature)
            if tile_id not in feature_collection["tiles"]:
                feature_collection["tiles"].append(tile_id)

    def _add_features_to_feature_collection(self, tile, layer_filter):
        """
         * Transforms all features of the specified tile into GeoJSON
         * The resulting GeoJSON feature will be applied to the features of the corresponding GeoJSON FeatureCollection
        :param tile:
        :return:
        """
        for layer_name in tile.decoded_data:
            layer = tile.decoded_data[layer_name]
            is_geojson_already = False
            if "isGeojson" in layer:
                is_geojson_already = layer["isGeojson"]
            if layer_filter and len(layer_filter) > 0:
                if layer_name not in layer_filter:
                    continue

            tile_id = tile.id()
            for feature in layer["features"]:
                if is_geojson_already:
                    geojson_features = [feature]
                    geo_type = geo_types_by_name[feature["geometry"]["type"]]
                    if geo_type == GeoTypes.POINT:
                        feature["properties"]["_symbol"] = self._get_poi_icon(feature)
                    assert geo_type is not None
                else:
                    if "extent" in layer:
                        extent = layer["extent"]
                    else:
                        extent = self._DEFAULT_EXTENT
                    geojson_features, geo_type = self._create_geojson_feature(feature, tile, extent)

                if geojson_features and len(geojson_features) > 0:
                    for f in geojson_features:
                        f["properties"]["_id"] = self._feature_count
                        f["properties"]["_col"] = tile.column
                        f["properties"]["_row"] = tile.row
                        f["properties"]["_zoom_level"] = tile.zoom_level
                        self._feature_count += 1

                    feature_collection = self._get_feature_collection(layer_name=layer_name,
                                                                      geo_type=geo_type,
                                                                      zoom_level=tile.zoom_level)
                    feature_collection["features"].extend(geojson_features)
                    if tile_id not in feature_collection["tiles"]:
                        feature_collection["tiles"].append(tile_id)

    def _get_feature_collection(self, layer_name, geo_type, zoom_level):
        name_and_geotype = (layer_name, geo_type)
        if name_and_geotype not in self.feature_collections_by_layer_name_and_geotype:
            self.feature_collections_by_layer_name_and_geotype[
                name_and_geotype] = self._get_empty_feature_collection(zoom_level=zoom_level, layer_name=layer_name)
        feature_collection = self.feature_collections_by_layer_name_and_geotype[name_and_geotype]
        return feature_collection

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
                                                mapper_func=lambda coords: self._get_absolute_coordinates(
                                                    coordinates=coords,
                                                    tile=tile,
                                                    extent=current_layer_tile_extent),
                                                all_out_of_bounds_func=lambda out_of_bounds: all_out_of_bounds.append(
                                                    out_of_bounds))

        if self._clip_tiles_at_tile_bounds and all(c is True for c in all_out_of_bounds):
            return None, None

        split_geometries = self._loading_options["merge_tiles"]
        geojson_features = VtReader._create_geojson_feature_from_coordinates(geo_type=geo_type,
                                                                             coordinates=coordinates,
                                                                             properties=properties,
                                                                             split_multi_geometries=split_geometries)

        return geojson_features, geo_type

    def _get_poi_icon(self, feature):
        """
         * Returns the name of the svg icon that will be applied in QGIS.
         * The resulting icon is determined based on class and subclass of the specified feature.
        :param feature: 
        :return: 
        """

        feature_class, feature_subclass = self._get_feature_class_and_subclass(feature)
        root_path = get_icons_directory()
        class_icon = "{}.svg".format(feature_class)
        class_subclass_icon = "{}.{}.svg".format(feature_class, feature_subclass)
        icon_name = "poi.svg"
        if os.path.isfile(os.path.join(root_path, class_subclass_icon)):
            icon_name = class_subclass_icon
        elif os.path.isfile(os.path.join(root_path, class_icon)):
            icon_name = class_icon
        return icon_name

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
    def _create_geojson_feature_from_coordinates(geo_type, coordinates, properties, split_multi_geometries):
        """
        * Returns a JSON object that represents a GeoJSON feature
        :param geo_type: 
        :param coordinates: 
        :param properties: 
        :return: 
        """
        assert coordinates is not None
        all_features = []

        coordinate_sets = [coordinates]

        type_string = geo_type
        is_multi_geometry = is_multi(geo_type, coordinates)
        if is_multi_geometry and not split_multi_geometries:
            type_string = "Multi{}".format(geo_type)
        elif is_multi_geometry and split_multi_geometries:
            coordinate_sets = []
            for coord_array in coordinates:
                coordinate_sets.append(coord_array)

        for c in coordinate_sets:
            feature_json = {
                "type": "Feature",
                "geometry": {
                    "type": type_string,
                    "coordinates": c
                },
                "properties": properties
            }
            all_features.append(feature_json)

        return all_features

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
