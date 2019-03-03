#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import *
import sys
import os
from io import BytesIO
from gzip import GzipFile
import multiprocessing

try:
    import simplejson as json
except ImportError:
    import json
import uuid
import traceback
from typing import Dict, List, Tuple, Optional

from qgis.core import (
    QgsProject,
    QgsVectorLayer,
    )

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication

if not os.environ.get("VTR_TESTS"):
    from .util.qgis_helper import get_loaded_layers_of_connection
    from .util.log_helper import info, critical, debug, remove_key
    from .util.tile_helper import get_all_tiles, get_code_from_epsg, clamp, Bounds, VectorTile
    from .util.feature_helper import (FeatureMerger,
                                      geo_types,
                                      is_multi,
                                      map_coordinates_recursive,
                                      GeoTypes,
                                      clip_features)
    from .util.file_helper import (get_styles,
                                   get_style_folder,
                                   assure_temp_dirs_exist,
                                   get_cache_entry,
                                   is_gzipped,
                                   get_geojson_file_name,
                                   get_icons_directory,
                                   cache_tile)
    from .util.tile_source import ServerSource, MBTilesSource, DirectorySource, AbstractSource
    from .util.connection import ConnectionTypes
    from .util.mp_helper import decode_tile_native, decode_tile_python, can_load_lib
else:
    from util.qgis_helper import get_loaded_layers_of_connection
    from util.log_helper import info, critical, debug, remove_key
    from util.tile_helper import get_all_tiles, get_code_from_epsg, clamp, Bounds, VectorTile
    from util.feature_helper import (FeatureMerger,
                                     geo_types,
                                     is_multi,
                                     map_coordinates_recursive,
                                     GeoTypes,
                                     clip_features)
    from util.file_helper import (get_styles,
                                  get_style_folder,
                                  assure_temp_dirs_exist,
                                  get_cache_entry,
                                  is_gzipped,
                                  get_geojson_file_name,
                                  get_icons_directory,
                                  cache_tile)
    from util.tile_source import ServerSource, MBTilesSource, DirectorySource, AbstractSource
    from util.connection import ConnectionTypes
    from util.mp_helper import decode_tile_native, decode_tile_python, can_load_lib

is_windows = sys.platform.startswith("win32")
if is_windows:
    # OSGeo4W does not bundle python in exec_prefix for python
    path = os.path.abspath(os.path.join(sys.exec_prefix, '../../bin/pythonw.exe'))
    multiprocessing.set_executable(path)
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

    _nr_tiles_to_process_serial = 30
    _layers_to_dissolve = []
    _zoom_level_delimiter = "*"
    _DEFAULT_EXTENT = 4096
    _id = str(uuid.uuid4())

    _all_tiles = []

    def __init__(self, iface, connection: dict):
        """
         * The mbtiles_path can also be an URL in zxy format: z=zoom, x=tile column, y=tile row
        :param iface: 
        :param connection:
        """
        QObject.__init__(self)
        if not connection:
            raise RuntimeError("The datasource is required")

        self._connection: dict = connection
        self._source: AbstractSource = self._create_source(connection)
        self._external_source: AbstractSource = self._create_source(connection)

        assure_temp_dirs_exist()
        self.iface = iface
        self.feature_collections_by_layer_name_and_geotype: Dict[Tuple[str, str], dict] = {}
        self.cancel_requested = False
        self._loaded_pois_by_id = {}
        self._clip_tiles_at_tile_bounds: False = None
        self._flush = False
        self._feature_count: int = None
        self._allowed_sources: List[str] = None

    def connection(self):
        return self._connection

    def set_allowed_sources(self, sources: List[str]):
        """
         * A list of layer sources (i.e. file paths) can be specified.
         These layers will later be ignored, i.e. not added.
        :param sources: The sources which can be created. If None, all are allowed, if empty list, none is allowed
        :return:
        """
        self._allowed_sources = sources

    def get_source(self) -> AbstractSource:
        """
         * Returns the source being used of the current reader. This method is intended for external use,
         i.e. from outside of this reader. SQlite objects must only be used in the thread they were created.
         As a result of this, each reader creates two identical connections, but one is created within and one
         outisde of the thread.
        :return:
        """

        return self._external_source

    def _create_source(self, connection: dict) -> AbstractSource:
        conn_type = connection["type"]
        if conn_type == ConnectionTypes.TileJSON:
            source = ServerSource(url=connection["url"])
        elif conn_type == ConnectionTypes.MBTiles:
            source = MBTilesSource(path=connection["path"])
        elif conn_type == ConnectionTypes.Directory:
            source = DirectorySource(path=connection["path"])
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

    def id(self) -> str:
        return self._id

    def _source_tile_limit_reached(self):
        if self._loading_options["max_tiles"]:
            self.tile_limit_reached.emit(self._loading_options["max_tiles"])

    def _source_progress_changed(self, progress: int):
        self._update_progress(progress=progress)

    def _source_max_progress_changed(self, max_progress: int):
        self._update_progress(max_progress=max_progress)

    def _source_message_changed(self, msg: str):
        self._update_progress(msg=msg)

    def _update_progress(self, show_dialog: bool = None, progress: int = None,
                         max_progress: int = None, msg: str = None):
        if progress is not None:
            self.progress_changed.emit(progress)
        if max_progress is not None:
            self.max_progress_changed.emit(max_progress)
        if msg:
            self.message_changed.emit(msg)
        if show_dialog:
            self.show_progress_changed.emit(show_dialog)

    def _get_empty_feature_collection(self, layer_name: str, zoom_level: int) -> dict:
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

    def cancel(self):
        """
         * Cancels the loading process.
        :return: 
        """
        self.cancel_requested = True
        if self._source:
            self._source.cancel()

    def _get_clamped_zoom_level(self) -> int:
        zoom_level = self._loading_options["zoom_level"]
        min_zoom = self._source.min_zoom()
        max_zoom = self._source.max_zoom()
        zoom_level = clamp(zoom_level, low=min_zoom, high=max_zoom)
        return zoom_level

    def _load_tiles(self):
        if not self._source or self.connection()["type"] == ConnectionTypes.MBTiles:
            # recreate source to assure the source belongs to the new thread, SQLite3 isn't happy about it otherwise
            self._source = self._create_source(self.connection())

        try:
            if can_load_lib():
                info("Native decoding supported!!!")
            else:
                bits = "32"
                if sys.maxsize > 2 ** 32:
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
            source_name = self._source.name()
            scheme = self._source.scheme()
            for t in all_tiles:
                if self.cancel_requested or (max_tiles and len(cached_tiles) >= max_tiles):
                    break

                decoded_data = get_cache_entry(cache_name=source_name, zoom_level=zoom_level, x=t[0], y=t[1])
                if decoded_data:
                    tile = VectorTile(scheme=scheme, zoom_level=zoom_level, x=t[0], y=t[1])
                    tile.decoded_data = decoded_data
                    cached_tiles.append(tile)
                    tiles_to_ignore.add((tile.column, tile.row))
                else:
                    tiles_to_load.add(t)

            remaining_nr_of_tiles = len(tiles_to_load)
            if max_tiles:
                if len(cached_tiles) + len(tiles_to_load) >= max_tiles:
                    remaining_nr_of_tiles = clamp(max_tiles - len(cached_tiles), low=0)
            info("{} tiles in cache. Max. {} will be loaded additionally.", len(cached_tiles), remaining_nr_of_tiles)
            if len(cached_tiles) > 0:
                if not self.cancel_requested:
                    self._process_tiles(cached_tiles, layer_filter)
                    self._all_tiles.extend(cached_tiles)

            debug("Loading data for zoom level '{}' source '{}'", zoom_level, self._source.name())

            if remaining_nr_of_tiles:
                tile_data_tuples = self._source.load_tiles(zoom_level=zoom_level,
                                                           tiles_to_load=tiles_to_load,
                                                           max_tiles=remaining_nr_of_tiles)
                if len(tile_data_tuples) > 0 and not self.cancel_requested:
                    tiles = self._decode_tiles(tile_data_tuples)
                    self._process_tiles(tiles, layer_filter)
                    for t in tiles:
                        cache_tile(cache_name=source_name, zoom_level=zoom_level, x=t.column, y=t.row,
                                   decoded_data=t.decoded_data)
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
            loaded_extent = self._get_extent(self._all_tiles, zoom_level, self._source.scheme())
            if not loaded_extent:
                loaded_extent = {}
            self.loading_finished.emit(zoom_level, loaded_extent)

    @staticmethod
    def _get_extent(tiles: List[VectorTile], zoom_level: int, scheme: str) -> Optional[Bounds]:
        loaded_tiles_x = [t.coord()[0] for t in tiles]
        loaded_tiles_y = [t.coord()[1] for t in tiles]
        if not tiles:
            return None

        bounds = Bounds.create(zoom=zoom_level,
                               x_min=min(loaded_tiles_x),
                               x_max=max(loaded_tiles_x),
                               y_min=min(loaded_tiles_y),
                               y_max=max(loaded_tiles_y),
                               scheme=scheme)
        return bounds

    def set_options(self, load_mask_layer=False, merge_tiles=True, clip_tiles=False, apply_styles=False, max_tiles=None,
                    layer_filter=None, is_inspection_mode=False):
        """
         * Specify the reader options
        :param is_inspection_mode:
        :param load_mask_layer:  If True the mask layer will also be loaded
        :param merge_tiles: If True neighbouring tiles and features will be merged
        :param clip_tiles: If True the features located outside the tile will be removed
        :param apply_styles: If True the default styles will be applied
        :param max_tiles: The maximum number of tiles to load
        :param layer_filter: A list of layers. If any layers are set, only these will be loaded. If the list is empty,
            all available layers will be loaded
        :return:
        """
        if layer_filter:
            layer_filter = list(layer_filter)
        self._loading_options = {
            'load_mask_layer': load_mask_layer,
            'merge_tiles': merge_tiles,
            'clip_tiles': clip_tiles,
            'apply_styles': apply_styles,
            'max_tiles': max_tiles,
            'layer_filter': layer_filter,
            'inspection_mode': is_inspection_mode
        }

    def load_tiles_async(self, bounds: Bounds):
        """
         * Loads the vector tiles from either a file or a URL and adds them to QGIS
        :param bounds:
        :return: 
        """
        zoom_level = bounds.zoom()
        info("Loading zoom level '{}', bounds: {}", zoom_level, bounds)
        self._loading_options["zoom_level"] = zoom_level
        self._loading_options["bounds"] = bounds
        # todo: better use QGIS 3 tasks for this
        _worker_thread = QThread(self.iface.mainWindow())
        self.moveToThread(_worker_thread)
        _worker_thread.started.connect(self._load_tiles)
        _worker_thread.start()

    @staticmethod
    def _get_pool() -> multiprocessing.Pool:
        nr_processors = 4
        try:
            nr_processors = multiprocessing.cpu_count()
        except NotImplementedError:
            info("CPU count cannot be retrieved. Falling back to default = 4")
        pool = multiprocessing.Pool(nr_processors)
        return pool

    def _decode_tiles(self, tiles_with_encoded_data):
        """
         * Decodes the PBF data from all the specified tiles and reports the progress
         * If a tile is loaded from the cache, the decoded_data is already set and doesn't have to be encoded
        :param tiles_with_encoded_data:
        :return:
        """
        clip_tiles = not self._loading_options["inspection_mode"]
        tiles_with_encoded_data = [(t[0], self._unzip(t[1]), clip_tiles) for t in tiles_with_encoded_data]

        if can_load_lib():
            decoder_func = decode_tile_native
        else:
            decoder_func = decode_tile_python

        tiles = []

        tile_data_tuples = []

        if len(tiles_with_encoded_data) <= self._nr_tiles_to_process_serial:
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
                QApplication.processEvents()
                remaining = rs._number_left
                index = nr_of_tiles - remaining
                progress = int(100.0 / nr_of_tiles * (index + 1))
                if progress != current_progress:
                    current_progress = progress
                    self._update_progress(progress=progress)
            if self.cancel_requested:
                pool.terminate()
            pool.join()

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

    def _process_tiles(self, tiles, layer_filter):
        """
         * Creates GeoJSON for all the specified tiles and reports the progress
        :param tiles: 
        :return: 
        """
        self._update_progress(msg="Processing features of {} tiles...".format(len(tiles)),
                              max_progress=len(tiles))
        for index, tile in enumerate(tiles):
            if self.cancel_requested:
                break
            if tile.decoded_data:
                self._all_tiles.append(tile)
                self._add_features_to_feature_collection(tile, layer_filter=layer_filter)
            self._update_progress(progress=index + 1)

    def _get_geojson_filename(self, layer_name, geo_type):
        return "{}.{}.{}".format(self._source.name().replace(" ", "_"), layer_name, geo_type)

    def _create_qgis_layers(self, merge_features, apply_styles, clip_tiles):
        """
         * Creates a hierarchy of groups and layers in qgis
        """
        own_layers: List[QgsVectorLayer] = get_loaded_layers_of_connection(self._connection["name"])
        for l in own_layers:
            name: str = l.name()
            geo_type = l.customProperty("VectorTilesReader/geo_type")
            if (name, geo_type) not in self.feature_collections_by_layer_name_and_geotype:
                if not bool(l.customProperty("VectorTilesReader/is_empty")):
                    info("Clearing layer: {}", name)
                    l.setCustomProperty("VectorTilesReader/is_empty", True)
                    self._update_layer_source(l.source(), self._get_empty_feature_collection(0, l.name()))
            else:
                l.setCustomProperty("VectorTilesReader/is_empty", False)

        self._update_progress(progress=0,
                              max_progress=len(self.feature_collections_by_layer_name_and_geotype),
                              msg="Creating layers...")
        layer_filter = self._loading_options["layer_filter"]

        clipping_bounds = None
        if merge_features:
            clipping_bounds = self._loading_options["bounds"]

        new_layers = []
        count = 0
        for layer_name, geo_type in self.feature_collections_by_layer_name_and_geotype:
            count += 1
            if self.cancel_requested:
                break
            if layer_filter and layer_name not in layer_filter:
                continue

            feature_collection = self.feature_collections_by_layer_name_and_geotype[(layer_name, geo_type)]
            zoom_level = feature_collection["zoom_level"]

            file_name = self._get_geojson_filename(layer_name, geo_type)
            file_path = get_geojson_file_name(file_name)

            layer = None
            if os.path.isfile(file_path):
                # file exists already. add the features of the collection to the existing collection
                # get the layer from qgis and update its source
                for l in own_layers:
                    if os.path.abspath(file_path).lower() == os.path.abspath(l.source()).lower():
                        layer = l
                        break
                if layer:
                    self._update_layer_source(file_path, feature_collection)
                    layer.reload()
                    if merge_features and geo_type in [GeoTypes.LINE_STRING, GeoTypes.POLYGON]:
                        merger = FeatureMerger(should_cancel_func=lambda: self.cancel_requested)
                        merger.merge_features(layer)
                    if clip_tiles:
                        clip_features(layer=layer,
                                      scheme=self._source.scheme(),
                                      bounds=clipping_bounds,
                                      should_cancel_func=lambda: self.cancel_requested)
            if not layer \
                    and (self._allowed_sources is None or file_path in self._allowed_sources) \
                    and (not layer_filter or layer_name in layer_filter):
                self._update_layer_source(file_path, feature_collection)
                layer = self._create_named_layer(json_src=file_path,
                                                 layer_name=layer_name,
                                                 geo_type=geo_type,
                                                 zoom_level=zoom_level)
                if merge_features and geo_type in [GeoTypes.LINE_STRING, GeoTypes.POLYGON]:
                    merger = FeatureMerger(should_cancel_func=lambda: self.cancel_requested)
                    merger.merge_features(layer)
                if clip_tiles:
                    clip_features(layer=layer,
                                  scheme=self._source.scheme(),
                                  bounds=clipping_bounds,
                                  should_cancel_func=lambda: self.cancel_requested)
                new_layers.append((layer_name, geo_type, layer))
            self._update_progress(progress=count + 1)

        self._update_progress(msg="Refresh layers...")

        if len(new_layers) > 0 and not self.cancel_requested:
            self._update_progress(msg="Adding new layers...")
            only_layers = list([layer_name_tuple[2] for layer_name_tuple in new_layers])
            QgsProject.instance().addMapLayers(only_layers, False)
        for name, geo_type, layer in new_layers:
            if self.cancel_requested:
                break
            self.add_layer_to_group.emit(layer)

        if apply_styles and not self.cancel_requested and new_layers:
            count = 0
            conn_name = self.connection()["name"]
            styles_folder = get_style_folder(conn_name)
            styles = get_styles(conn_name)
            self._update_progress(progress=0, max_progress=len(new_layers), msg="Styling layers...")
            for name, geo_type, layer in new_layers:
                count += 1
                if self.cancel_requested:
                    break
                VtReader._apply_named_style(existing_styles=styles,
                                            style_dir=styles_folder,
                                            layer=layer,
                                            geo_type=geo_type)
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
    def _apply_named_style(existing_styles, style_dir, layer, geo_type):
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
                name,
                "transparent.{}".format(geo_type.lower()),
                geo_type.lower()
            ]
            for p in styles:
                style_name = "{}.qml".format(p).lower()
                if style_name in existing_styles:
                    style_path = os.path.join(style_dir, style_name)
                    res = layer.loadNamedStyle(style_path)
                    if res[1]:  # Style loaded
                        layer.setCustomProperty("VectorTilesReader/layerStyle", style_path)
                        break
        except:
            critical("Loading style failed: {}", sys.exc_info())

    def _create_named_layer(self, json_src, layer_name, geo_type, zoom_level):
        """
         * Creates a QgsVectorLayer and adds it to the group specified by layer_target_group
         * Invalid geometries will be removed during the process of merging features over tile boundaries
        """

        source_url = self._source.source()
        layer = QgsVectorLayer(json_src, layer_name, "ogr")

        layer.setCustomProperty("VectorTilesReader/vector_tile_source", self._connection["name"])
        layer.setCustomProperty("VectorTilesReader/vector_tile_url", source_url)
        layer.setCustomProperty("VectorTilesReader/zoom_level", zoom_level)
        layer.setCustomProperty("VectorTilesReader/geo_type", geo_type)
        layer.setShortName(layer_name)
        layer.setDataUrl(remove_key(source_url))
        layer.setAttribution(self._source.attribution())
        # layer.setAttributionUrl("")
        # layer.setAbstract()
        return layer

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
            if is_geojson_already:
                for geo_type_id in geo_types:
                    geo_type = geo_types[geo_type_id]
                    features = layer[geo_type]
                    if features:
                        feature_collection = self._get_feature_collection(layer_name=layer_name,
                                                                          geo_type=geo_type,
                                                                          zoom_level=tile.zoom_level)
                        feature_collection["features"].extend(features)
                        if tile_id not in feature_collection["tiles"]:
                            feature_collection["tiles"].append(tile_id)
            else:
                for feature in layer["features"]:
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
                            f["properties"]["_zoom"] = tile.zoom_level
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
