# -*- coding: utf-8 -*-

""" THIS COMMENT MUST NOT REMAIN INTACT

GNU GENERAL PUBLIC LICENSE

Copyright (c) 2017 geometalab HSR

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

"""

import os
import re
import site
import sys
import traceback
import ast

from builtins import map
from builtins import str
import logging
from .util.log_helper import info, critical, debug
from .util.vtr_2to3 import *
from .util.network_helper import url_exists, load_url
from .util.tile_helper import (
    latlon_to_tile,
    get_zoom_by_scale,
    clamp,
    get_code_from_epsg,
    get_tile_bounds,
    tile_to_latlon,
    extent_overlap_bounds,
    center_tiles_equal,
    clamp_bounds,
    convert_coordinate,
    WORLD_BOUNDS)

from .ui.dialogs import AboutDialog, ConnectionsDialog
from .util.file_helper import (
    get_icons_directory,
    clear_cache,
    get_plugin_directory,
    get_temp_dir)

# try:
#     pth = 'C:\\Program Files\\JetBrains\\PyCharm 2017.2.3\\debug-eggs\\pycharm-debug.egg'
#     if pth not in sys.path:
#         sys.path.append(pth)
#     import pydevd
#     pydevd.settrace('localhost', port=53100, stdoutToServer=True, stderrToServer=True)
# except:
#     pass


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


# noinspection PyUnresolvedReferences,PyArgumentList
class VtrPlugin():
    _dialog = None
    _model = None
    _reload_button_text = "Load features overlapping the view extent"
    add_layer_action = None

    def _get_zoom_for_current_map_scale(self):
        current_scale = self._get_current_map_scale()
        return get_zoom_by_scale(current_scale)

    def _get_current_map_scale(self):
        canvas = self.iface.mapCanvas()
        current_scale = int(round(canvas.scale()))
        return current_scale

    def __init__(self, iface):
        self.iface = iface
        iface.newProjectCreated.connect(self._on_project_change)
        iface.projectRead.connect(self._on_project_change)
        QgsMapLayerRegistry.instance().layerWillBeRemoved.connect(self._on_remove)
        self._add_path_to_dependencies_to_syspath()
        self.settings = QSettings("Vector Tile Reader", "vectortilereader")
        self._clear_cache_when_version_changed()
        self.connections_dialog = ConnectionsDialog(self._get_initial_browse_directory())
        self.connections_dialog.on_directory_change.connect(self._on_browse_dir_change)
        self.connections_dialog.on_connect.connect(self._on_connect)
        self.connections_dialog.on_add.connect(self._on_add_layer)
        self.connections_dialog.on_zoom_change.connect(self._on_zoom_change)
        self.progress_dialog = None
        self._current_reader = None
        self._add_path_to_icons()
        self._current_layer_filter = []
        self._auto_zoom = False
        self._currrent_connection_name = None
        self._current_zoom = None
        self._current_scale = None
        self._loaded_extent = None
        self._loaded_scale = None
        self._is_loading = False
        self.iface.mapCanvas().xyCoordinates.connect(self._handle_mouse_move)
        self._debouncer = SignalDebouncer(timeout=500,
                                          signals=[
                                              # self.iface.mapCanvas().scaleChanged,  # doesn't seem to be required,
                                              # is fired anyway, even when only the extent has changed
                                              self.iface.mapCanvas().extentsChanged
                                          ],
                                          predicate=self._have_extent_or_scale_changed)
        self._debouncer.on_notify.connect(self._handle_map_scale_or_extents_changed)
        self._debouncer.on_notify_in_pause.connect(self._on_scale_or_extent_change_during_pause)
        self._scale_to_load = None
        self._extent_to_load = None
        self._current_extent = None
        self.message_bar_item = None
        self.progress_bar = None
        self._inspection_mode_active = False
        self._current_reader_sources = None
        self._debouncer.start()

    def _on_remove(self, id):
        if QgsMapLayerRegistry and id:
            layers = QgsMapLayerRegistry.instance().mapLayers()
            if self._current_reader_sources is None:
                self._update_current_reader_sources()
            assert self._current_reader_sources
            if id in layers:
                removed_layer = layers[id]
                src = removed_layer.source()
                if src in self._current_reader_sources:
                    self._current_reader_sources.remove(src)

    def initGui(self):
        self.popupMenu = QMenu(self.iface.mainWindow())
        self.open_connections_action = self._create_action("Add Vector Tiles Layer...", "mActionAddVectorTilesReader.svg",
                                                           self._show_connections_dialog)
        self.reload_action = self._create_action(self._reload_button_text, "reload.svg",
                                                 self._load_features_overlapping_tile_extent, False)
        self.clear_cache_action = self._create_action("Clear cache", "delete.svg", clear_cache)
        self.about_action = self._create_action("About", "info.svg", self.show_about)
        self.iface.insertAddLayerAction(self.open_connections_action)  # Add action to the menu: Layer->Add Layer
        self.popupMenu.addAction(self.open_connections_action)
        self.popupMenu.addAction(self.reload_action)
        self.popupMenu.addAction(self.clear_cache_action)
        self.popupMenu.addAction(self.about_action)
        self.toolButton = QToolButton()
        self.toolButton.setMenu(self.popupMenu)
        self.toolButton.setDefaultAction(self.open_connections_action)
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButtonAction = self.iface.layerToolBar().addWidget(self.toolButton)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.open_connections_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.reload_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.clear_cache_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.about_action)
        info("Vector Tile Reader Plugin loaded...")
        self._connect_to_first_source()

    def _connect_to_first_source(self):
        proj = QgsProject.instance()
        conn = proj.readEntry("VectorTilesReader", "current_connection", None)[0]
        if conn:
            conn = ast.literal_eval(conn)
            self.connections_dialog.connect(conn)
            self._debouncer.start()

    def _on_browse_dir_change(self, diretory_path):
        self.settings.setValue("last_directory", diretory_path)

    def _get_initial_browse_directory(self):
        """
         * If qgis is started in a specific folder, this folder will be used as initial directory when browsing sources
          Otherwise, the sample data folder will be opened.
        :return:
        """
        last_browse_directory = self.settings.value("last_directory", None)
        if not last_browse_directory:
            last_browse_directory = os.path.expanduser("~")
        return last_browse_directory

    def _clear_cache_when_version_changed(self):
        latest_version = self._get_plugin_version()
        local_version = self.settings.value("version", None)
        if not local_version or local_version != latest_version:
            info("Plugin version changed from '{}' to '{}'. Cache will be cleared...", local_version, latest_version)
            clear_cache()
        self.settings.setValue("version", latest_version)

    @staticmethod
    def _get_plugin_version():
        version = None
        with open(os.path.join(get_plugin_directory(), 'metadata.txt'), 'r') as f:
            content = f.read()
        match = re.search(r"version=\d+\.\d+.\d+", content)
        if match:
            version = match.group().replace("version=", "")
        return version

    def _on_project_change(self):
        self.iface.mainWindow().statusBar().showMessage("")
        self._debouncer.stop()
        self._cancel_load()
        self.connections_dialog.set_layers([])
        if self._current_reader:
            self._current_reader.shutdown()
            self._current_reader = None
        self._connect_to_first_source()

    def _load_features_overlapping_tile_extent(self):
        clear_cache()
        self._reload_tiles(ignore_limit=True)

    def _have_extent_or_scale_changed(self):
        if self._current_reader:
            has_scale_changed = self._has_scale_changed()[0]
            has_extent_changed = self._has_extent_changed()[0]
            return has_scale_changed or has_extent_changed
        else:
            return False

    def _on_scale_or_extent_change_during_pause(self):
        assert self._current_reader
        self._scale_to_load = None
        self._extent_to_load = None

        has_scale_changed, new_target_scale, has_scale_increased = self._has_scale_changed()
        if has_scale_changed:
            self._scale_to_load = None
        else:
            has_extent_changed, new_target_extent = self._has_extent_changed()
            if has_extent_changed:
                self._extent_to_load = new_target_extent

        if self._is_loading and (self._scale_to_load or self._extent_to_load):
            info("Cancelling loading due to new request...")
            self._cancel_load()

    def _on_add_layer(self, connection, selected_layers):
        assert connection
        self._current_reader_sources = None
        self._create_styles(connection)
        self._assure_qgis_groups_exist(connection["name"], True)

        crs_string = self._current_reader.get_source().crs()
        self._init_qgis_map(crs_string)

        scheme = self._current_reader.get_source().scheme()
        zoom = self._get_current_zoom()

        if not self._loaded_extent:
            extent = get_tile_bounds(zoom, WORLD_BOUNDS, 4326)
        else:
            extent = self._get_visible_extent_as_tile_bounds(zoom=zoom)

        bounds = self._current_reader.get_source().bounds_tile(zoom)
        info("Bounds of source: {}", bounds)
        is_within_bounds = self.is_extent_within_bounds(extent, bounds)
        if not is_within_bounds:
            info("setting qgis extent ")
            self._set_qgis_extent(zoom=zoom, scheme=scheme, bounds=bounds)

        if not self._is_valid_qgis_extent(extent_to_load=extent, zoom=zoom):
            info("QGIS extent is not valid, replacing by source bounds")
            extent = self._current_reader.get_source().bounds_tile(zoom)

        keep_dialog_open = self.connections_dialog.keep_dialog_open()
        if not keep_dialog_open:
            self.connections_dialog.close()
        self._load_tiles(options=self.connections_dialog.options,
                         layers_to_load=selected_layers,
                         bounds=extent,
                         is_add=True)
        self._current_layer_filter = selected_layers

    def _handle_map_scale_or_extents_changed(self):
        if not self._is_loading and self._current_reader and self.connections_dialog.options.auto_zoom_enabled():
            has_scale_changed, new_scale, has_scale_increased = self._has_scale_changed()
            has_extent_changed, new_extent = self._has_extent_changed()

            self._scale_to_load = None
            self._extent_to_load = None

            is_new_extent_within_loaded_extent = self._loaded_extent \
                                                 and self._loaded_extent["x_min"] <= new_extent["x_min"] <= \
                                                     self._loaded_extent["x_max"] \
                                                 and self._loaded_extent["x_min"] <= new_extent["x_max"] <= \
                                                     self._loaded_extent["x_max"] \
                                                 and self._loaded_extent["y_min"] <= new_extent["y_min"] <= \
                                                     self._loaded_extent["y_max"] \
                                                 and self._loaded_extent["y_min"] <= new_extent["y_max"] <= \
                                                     self._loaded_extent["y_max"]

            old_scale = self._loaded_scale

            new_zoom = self._get_zoom_for_current_map_scale()
            min_zoom = self._current_reader.get_source().min_zoom()
            max_zoom = self._current_reader.get_source().max_zoom()
            new_zoom = clamp(new_zoom, low=min_zoom, high=max_zoom)

            has_zoom_changed = new_zoom != self._current_zoom
            if new_scale and has_scale_changed and has_zoom_changed:
                self._loaded_scale = new_scale
                self._loaded_extent = new_extent

                info("Reloading due to scale change from '{}' (zoom {}) to '{}' (zoom {})", old_scale,
                     self._current_zoom, new_scale, new_zoom)
                self._handle_scale_change(new_scale)
            elif has_extent_changed and not is_new_extent_within_loaded_extent:
                tile_limit = self.connections_dialog.options.tile_number_limit()
                extent_results_equal = False
                if tile_limit and self._loaded_extent:
                    extent_results_equal = center_tiles_equal(tile_limit, self._loaded_extent, new_extent)

                if not extent_results_equal:
                    info("Reloading due to extent change from {} to {}", self._loaded_extent, new_extent)
                    self._loaded_scale = new_scale
                    self._loaded_extent = new_extent
                    self._reload_tiles(overwrite_extent=new_extent)

    def _on_zoom_change(self):
        zoom = self._get_zoom_of_current_mode()
        if zoom:
            self._update_nr_of_tiles(zoom)

    def _update_nr_of_tiles(self, zoom):
        bounds = self._get_visible_extent_as_tile_bounds(zoom=zoom)
        nr_of_tiles = bounds["width"] * bounds["height"]
        self.connections_dialog.set_nr_of_tiles(nr_of_tiles)

    def _on_connect(self, connection):
        proj = QgsProject.instance()
        proj.writeEntry("VectorTilesReader", "current_connection", str(connection))
        self._currrent_connection_name = connection["name"]
        self.reload_action.setText("{} ({})".format(self._reload_button_text, self._currrent_connection_name))
        if self._current_reader and self._current_reader.connection() != connection:
            self._current_reader.shutdown()
            self._current_reader.progress_changed.disconnect()
            self._current_reader.max_progress_changed.disconnect()

            self._current_reader.message_changed.disconnect()
            self._current_reader.show_progress_changed.disconnect()
            self._current_reader = None
        if not self._current_reader:
            reader = self._create_reader(connection=connection)
            self._current_reader = reader
        if self._current_reader:
            layers = self._current_reader.get_source().vector_layers()
            self.connections_dialog.set_layers(layers)
            self.connections_dialog.options.set_zoom(min_zoom=self._current_reader.get_source().min_zoom(),
                                                     max_zoom=self._current_reader.get_source().max_zoom())
            self.reload_action.setEnabled(True)
        else:
            self.connections_dialog.set_layers([])
            self.reload_action.setEnabled(False)
            self.reload_action.setText(self._reload_button_text)
        self._update_current_reader_sources()

    def _update_current_reader_sources(self):
        own_layers = self._get_all_own_layers()
        if own_layers:
            self._current_reader_sources = list(map(lambda l: l.source(), own_layers))
        else:
            self._current_reader_sources = None

    def _create_styles(self, connection):
        if "style" not in connection or not connection["style"]:
            return
        url = connection["style"]
        info("Creating styles from: {}", url)
        from mapboxstyle2qgis import core
        core.register_qgis_expressions()
        if not url_exists(url):
            info("StyleJSON not found. URL invalid?")
        else:
            output_directory = get_temp_dir(os.path.join("styles", connection["name"]))
            status, data = load_url(url)
            if status == 200:
                try:
                    info("Styles will be written to: {}", output_directory)
                    core.generate_styles(data, output_directory, web_request_executor=self._load_style_data)
                    if self.connections_dialog.options.set_background_color_enabled():
                        background_color = core.get_background_color(data)
                        info("Setting background color: {}", background_color)
                        self._set_background_color(background_color)
                except:
                    tb = ""
                    if traceback:
                        tb = traceback.format_exc()
                    critical("Style generation failed: {}, {}", sys.exc_info(), tb)
            else:
                info("Loading StyleJSON failed: HTTP status {}", status)

    @staticmethod
    def _load_style_data(url):
        status, data = load_url(url)
        return data

    def reader_cancelled(self):
        info("cancelled")
        self._is_loading = False
        self.handle_progress_update(show_progress=False)
        if self._auto_zoom:
            extent = self._extent_to_load
            reload_immediate = self._scale_to_load is not None or extent
            if reload_immediate:
                if self._scale_to_load:
                    self._loaded_scale = self._scale_to_load
                if extent:
                    self._loaded_extent = extent

                self._extent_to_load = None
                self._scale_to_load = None
                self._reload_tiles(overwrite_extent=extent)
            else:
                self._debouncer.start()

    def reader_limit_exceeded_message(self, limit):
        """
        * Shows a message in QGIS that the nr of tiles has been restricted by the tile limit set in the options
        :return:
        """
        if limit:
            self.iface.messageBar().pushMessage(
                "Only {} tiles were loaded according to the limit in the options".format(limit),
                level=QgsMessageBar.WARNING,
                duration=5)

    def _has_extent_changed(self):
        scale = self._scale_to_load
        if not scale:
            scale = self._get_current_map_scale()

        if self._extent_to_load:
            new_extent = self._extent_to_load
        else:
            zoom = get_zoom_by_scale(scale)
            max_zoom = self._current_reader.get_source().max_zoom()
            min_zoom = self._current_reader.get_source().min_zoom()
            zoom = clamp(zoom, low=min_zoom, high=max_zoom)
            new_extent = self._get_visible_extent_as_tile_bounds(zoom)
            source_bounds = self._current_reader.get_source().bounds_tile(zoom)
            new_extent = clamp_bounds(bounds_to_clamp=new_extent, clamp_values=source_bounds)

        has_changed = not self._loaded_extent or new_extent["zoom"] != self._loaded_extent["zoom"] \
                      or new_extent["x_min"] != self._loaded_extent["x_min"] \
                      or new_extent["y_min"] != self._loaded_extent["y_min"]
        return has_changed, new_extent

    def _has_scale_changed(self):
        new_scale = self._get_current_map_scale()
        if self._scale_to_load:
            new_scale = self._scale_to_load

        has_changed = new_scale != self._loaded_scale
        scale_increased = self._current_scale is None or new_scale > self._current_scale
        return has_changed, new_scale, scale_increased

    def _handle_scale_change(self, new_scale):
        scale_increased = self._current_scale is None or new_scale > self._current_scale
        self._current_scale = new_scale
        max_zoom = self._current_reader.get_source().max_zoom()
        new_zoom = get_zoom_by_scale(new_scale)
        if new_zoom > max_zoom:
            new_zoom = max_zoom
        current_zoom = self._current_zoom
        if new_zoom != current_zoom or (scale_increased and new_scale > self._loaded_scale):
            self._loaded_scale = new_scale
            self._reload_tiles()

    def _get_qgis_crs(self):
        canvas = self.iface.mapCanvas()
        return get_code_from_epsg(canvas.mapSettings().destinationCrs().authid())

    def _handle_mouse_move(self, pos):
        if not self._current_reader:
            return

        qgis_zoom = self._get_zoom_for_current_map_scale()
        min_zoom = self._current_reader.get_source().min_zoom()
        max_zoom = self._current_reader.get_source().max_zoom()
        zoom = clamp(qgis_zoom, low=min_zoom, high=max_zoom)

        lon = pos[0]
        lat = pos[1]

        current_crs = self._get_qgis_crs()
        x, y = latlon_to_tile(zoom=zoom, lat=lat, lng=lon, source_crs=current_crs)
        mapbox_x, mapbox_y = latlon_to_tile(zoom=zoom, lat=lat, lng=lon, source_crs=3857)

        mapbox_addition = ""
        if current_crs != 3857:
            mapbox_addition = "  (Mapbox-Tile: {zoom},{mapbox_x},{mapbox_y})".format(zoom=zoom,
                                                                                     mapbox_x=mapbox_x,
                                                                                     mapbox_y=mapbox_y)

        msg = "Zoom: {qgis_zoom}   Tile: {zoom},{x},{y} {mapbox}".format(qgis_zoom=qgis_zoom,
                                                                         zoom=zoom,
                                                                         x=x,
                                                                         y=y,
                                                                         mapbox=mapbox_addition)
        self.iface.mainWindow().statusBar().showMessage(msg)

    @staticmethod
    def _add_path_to_icons():
        icons_directory = get_icons_directory()
        current_paths = QgsApplication.svgPaths()
        if icons_directory not in current_paths:
            current_paths.append(icons_directory)
            QgsApplication.setDefaultSvgPaths(current_paths)

    def _show_connections_dialog(self):
        zoom = self._get_zoom_of_current_mode()
        self._update_nr_of_tiles(zoom=zoom)
        current_connection = None
        if self._current_reader:
            current_connection = self._current_reader.connection()
        self.connections_dialog.show(current_connection)

    def _get_zoom_of_current_mode(self):
        zoom = 0
        manual_zoom = self.connections_dialog.options.manual_zoom()
        if self.connections_dialog.options.auto_zoom_enabled():
            zoom = self._get_zoom_for_current_map_scale()
            if self._current_reader:
                min_zoom = self._current_reader.get_source().min_zoom()
                max_zoom = self._current_reader.get_source().max_zoom()
                zoom = clamp(zoom, low=min_zoom, high=max_zoom)
        elif manual_zoom:
            zoom = manual_zoom
        else:
            if self._current_reader:
                zoom = self._current_reader.get_source().max_zoom()
        return zoom

    def _get_all_own_layers(self):
        layers = []
        if self._current_reader:
            for l in list(QgsMapLayerRegistry.instance().mapLayers().values()):
                data_url = l.dataUrl().lower()
                if data_url and self._current_reader.get_source().source().lower().startswith(data_url):
                    layers.append(l)
        return layers

    def _reload_tiles(self, overwrite_extent=None, ignore_limit=False):
        if self._debouncer.is_running():
            self._debouncer.pause()
        if self._current_reader:
            zoom = self._get_current_zoom()
            auto_zoom_enabled = self.connections_dialog.options.auto_zoom_enabled()
            flush_loaded_layers = auto_zoom_enabled and zoom != self._current_zoom
            self._current_zoom = zoom
            if flush_loaded_layers:
                self._current_reader.flush_layers_of_other_zoom_level = True

            if overwrite_extent:
                bounds = overwrite_extent
            else:
                bounds = self._get_visible_extent_as_tile_bounds(zoom=zoom)

            if self.connections_dialog.options.auto_zoom_enabled():
                self._current_reader.always_overwrite_geojson(True)

            self._load_tiles(options=self.connections_dialog.options,
                             layers_to_load=self._current_layer_filter,
                             bounds=bounds,
                             ignore_limit=ignore_limit)

    def _get_current_extent_as_wkt(self):
        return self.iface.mapCanvas().extent().asWktCoordinates()

    def _get_visible_extent_as_tile_bounds(self, zoom):
        extent = self.iface.mapCanvas().mapSettings().visibleExtent()
        x_min = extent.xMinimum()
        x_max = extent.xMaximum()
        y_min = extent.yMinimum()
        y_max = extent.yMaximum()
        scheme = "xyz"
        if self._current_reader:
            scheme = self._current_reader.get_source().scheme()
        if scheme == "xyz":
            bounds = [x_min, y_min, x_max, y_max]
        else:
            bounds = [x_min, y_max, x_max, y_min]
        # the source_crs is 3857, even if the actual data is in another (21781 for example)
        # the reason is to be fully compatible with the mapbox apis. Ask Petr Pridal @ klokan for details
        # the tile bounds returned here must have the same scheme as the source, otherwise thing's get pretty irritating
        tile_bounds = get_tile_bounds(zoom, bounds=bounds, scheme=scheme, source_crs=3857)
        return tile_bounds

    @staticmethod
    def show_about():
        AboutDialog().show()

    def _is_valid_qgis_extent(self, extent_to_load, zoom):
        source_bounds = self._current_reader.get_source().bounds_tile(zoom)
        if source_bounds and not source_bounds["x_min"] <= extent_to_load["x_min"] <= source_bounds["x_max"] \
                and not source_bounds["x_min"] <= extent_to_load["x_max"] <= source_bounds["x_max"] \
                and not source_bounds["y_min"] <= extent_to_load["y_min"] <= source_bounds["y_max"] \
                and not source_bounds["y_min"] <= extent_to_load["y_max"] <= source_bounds["y_max"]:
            return False
        return True

    @staticmethod
    def is_extent_within_bounds(extent, bounds):
        is_within = True
        if bounds and extent:
            x_min_within = extent['x_min'] >= bounds['x_min']
            y_min_within = extent['y_min'] >= bounds['y_min']
            x_max_within = extent['x_max'] <= bounds['x_max']
            y_max_within = extent['y_max'] <= bounds['y_max']
            is_within = x_min_within and y_min_within and x_max_within and y_max_within
        else:
            debug("Bounds not available on source. Assuming extent is within bounds")
        return is_within

    def _get_current_zoom(self):
        zoom = None
        min_zoom = None
        max_zoom = None
        if self._current_reader:
            min_zoom = self._current_reader.get_source().min_zoom()
            max_zoom = self._current_reader.get_source().max_zoom()
            zoom = max_zoom
        if zoom is None:
            zoom = 14
        manual_zoom = self.connections_dialog.options.manual_zoom()
        if manual_zoom is not None:
            zoom = manual_zoom
        if self.connections_dialog.options.auto_zoom_enabled():
            zoom = self._get_zoom_for_current_map_scale()
        zoom = clamp(zoom, low=min_zoom, high=max_zoom)
        return zoom

    def _set_qgis_extent(self, zoom, scheme, bounds):
        """
         * Sets the current extent of the QGIS map canvas to the specified bounds
        :return: 
        """
        min_xy = tile_to_latlon(zoom, bounds["x_min"], bounds["y_min"], scheme=scheme)
        max_xy = tile_to_latlon(zoom, bounds["x_max"], bounds["y_max"], scheme=scheme)
        min_pos = convert_coordinate(900913, self._get_qgis_crs(), lat=min_xy[1], lng=min_xy[0])
        max_pos = convert_coordinate(900913, self._get_qgis_crs(), lat=min_xy[1], lng=max_xy[0])

        map_min_pos = QgsPoint(min_pos[0], min_pos[1])
        map_max_pos = QgsPoint(max_pos[0], max_pos[1])
        rect = QgsRectangle(map_min_pos, map_max_pos)
        self.iface.mapCanvas().setExtent(rect)
        self.iface.mapCanvas().refresh()

    def _init_qgis_map(self, crs_string):
        center = tuple(map(lambda n: int(round(n)), self.iface.mapCanvas().extent().center()))
        crs = QgsCoordinateReferenceSystem(crs_string)
        if not crs.isValid():
            crs = QgsCoordinateReferenceSystem("EPSG:3857")
            crs_string = 3857
        try:
            self.iface.mapCanvas().mapRenderer().setDestinationCrs(crs)
        except AttributeError:
            self.iface.mapCanvas().setDestinationCrs(crs)

        x, y = convert_coordinate(4326, crs_string, lat=46.95592, lng=7.42078)
        if center == (0, 0):
            self.iface.mapCanvas().setCenter(QgsPoint(x, y))
            self.iface.mapCanvas().zoomScale(88687108)

    def _cancel_load(self):
        if self._current_reader:
            self._current_reader.cancel()

    def _create_action(self, title, icon, callback, is_enabled=True):
        new_action = QAction(QIcon(':/plugins/vector_tiles_reader/{}'.format(icon)), title, self.iface.mainWindow())
        new_action.triggered.connect(callback)
        new_action.setEnabled(is_enabled)
        return new_action

    def _has_layers_of_current_connection(self):
        qgis_layers = QgsMapLayerRegistry.instance().mapLayers()
        layers = filter(lambda t: t[1].customProperty("VectorTilesReader/vector_tile_source") ==
                                  self._current_reader.get_source().source(), iter(qgis_layers.items()))
        if layers:
            return len(list(layers))
        return 0

    def _load_tiles(self, options, layers_to_load, bounds, ignore_limit=False, is_add=False):
        self._current_extent = bounds
        if self._debouncer.is_running():
            if is_add:
                self._debouncer.stop()
            else:
                self._debouncer.pause()

        if not is_add and not self._has_layers_of_current_connection():
            info("cancel load due to missing layers")
            return

        merge_tiles = options.merge_tiles_enabled()
        apply_styles = options.apply_styles_enabled()
        tile_limit = options.tile_number_limit()
        load_mask_layer = options.load_mask_layer_enabled()
        inspection_mode = options.is_inspection_mode()
        if self._inspection_mode_active != inspection_mode:
            clear_cache()
        self._inspection_mode_active = inspection_mode
        self._auto_zoom = options.auto_zoom_enabled()
        if ignore_limit:
            tile_limit = None
        manual_zoom = options.manual_zoom()
        clip_tiles = options.clip_tiles()

        reader = self._current_reader
        if not reader:
            self._is_loading = False
        else:
            try:
                max_zoom = reader.get_source().max_zoom()
                min_zoom = reader.get_source().min_zoom()
                if self._auto_zoom:
                    zoom = self._get_zoom_for_current_map_scale()
                    zoom = clamp(zoom, low=min_zoom, high=max_zoom)
                else:
                    zoom = max_zoom
                    if manual_zoom is not None:
                        zoom = manual_zoom
                self._current_zoom = zoom

                source_bounds = reader.get_source().bounds_tile(zoom)
                if source_bounds and not extent_overlap_bounds(bounds, source_bounds) \
                        and not extent_overlap_bounds(source_bounds, bounds):
                    info("The current map extent is not within the bounds of the source. The extent to load "
                         "will be set to the bounds of the source. Map extent: '{}', source bounds: '{}'", bounds,
                         source_bounds)
                    bounds = source_bounds

                reader.set_allowed_sources(self._current_reader_sources)
                reader.set_options(load_mask_layer=load_mask_layer, merge_tiles=merge_tiles, clip_tiles=clip_tiles,
                                   apply_styles=apply_styles, max_tiles=tile_limit, layer_filter=layers_to_load,
                                   is_inspection_mode=inspection_mode)
                self._is_loading = True
                reader.load_tiles_async(zoom_level=zoom, bounds=bounds)
            except Exception as e:
                critical("An exception occured: {}", e)
                tb_lines = traceback.format_tb(sys.exc_traceback)
                tb_text = ""
                for line in tb_lines:
                    tb_text += line
                critical("{}", tb_text)
                self.iface.messageBar().pushMessage(
                    "Something went horribly wrong. Please have a look at the log.",
                    level=QgsMessageBar.CRITICAL,
                    duration=5)
                self._is_loading = False

    def _set_background_color(self, color_string):
        color = QColor(color_string)
        # Write it to the project (will still need to be saved!)
        QgsProject.instance().writeEntry("Gui", "/CanvasColorRedPart", color.red())
        QgsProject.instance().writeEntry("Gui", "/CanvasColorGreenPart", color.green())
        QgsProject.instance().writeEntry("Gui", "/CanvasColorBluePart", color.blue())
        # And apply for the current session
        self.iface.mapCanvas().setCanvasColor(color)
        self.iface.mapCanvas().refresh()

    def refresh_layers(self):
        for layer in self.iface.mapCanvas().layers():
            layer.triggerRepaint()

    def _create_reader(self, connection):
        # A lazy import is required because the vtreader depends on the external libs
        from .vt_reader import VtReader
        reader = None
        try:
            reader = VtReader(self.iface, connection=connection)
            reader.progress_changed.connect(self.reader_progress_changed)
            reader.max_progress_changed.connect(self.reader_max_progress_changed)
            reader.show_progress_changed.connect(self.reader_show_progress_changed)
            reader.message_changed.connect(self.reader_message_changed)
            reader.loading_finished.connect(self.reader_loading_finished)
            reader.tile_limit_reached.connect(self.reader_limit_exceeded_message)
            reader.cancelled.connect(self.reader_cancelled)
            reader.add_layer_to_group.connect(self.add_layer_to_group)
        except RuntimeError:
            QMessageBox.critical(None, "Error", str(sys.exc_info()[1]))
            critical(str(sys.exc_info()[1]))
        return reader

    def add_layers(self, layers):
        info("add layers: {}", layers)
        QgsMapLayerRegistry.instance().addMapLayers(layers, False)

    def add_layer_to_group(self, layer):
        root_group_name = self._currrent_connection_name
        root = QgsProject.instance().layerTreeRoot()
        root_group = root.findGroup(root_group_name)
        if not root_group:
            root_group = root.addGroup(root_group_name)
        layer_group = root_group.findGroup(layer.name())
        if not layer_group:
            layer_group = root_group.addGroup(layer.name())
        layer_group.addLayer(layer)

    def reader_loading_finished(self, loaded_zoom_level, loaded_extent):
        self._loaded_extent = self._current_extent
        self.handle_progress_update(show_progress=False)

        auto_zoom = self._auto_zoom

        self._loaded_scale = self._get_current_map_scale()
        self.refresh_layers()
        if loaded_extent:
            info("Loading of zoom level {} complete! Loaded extent: {}", loaded_zoom_level, loaded_extent)
        else:
            info("Loading of zoom level {} complete! No extent loaded.", loaded_zoom_level)

        if loaded_extent and (not auto_zoom or (auto_zoom and self._loaded_scale is None)):
            scheme = self._current_reader.get_source().scheme()
            visible_extent = self._get_visible_extent_as_tile_bounds(loaded_zoom_level)
            overlap = extent_overlap_bounds(visible_extent, loaded_extent)
            if not overlap:
                info("Changing QGIS extent as it's not overlapping with the loaded extent")
                self._set_qgis_extent(zoom=loaded_zoom_level, scheme=scheme, bounds=loaded_extent)

        self._is_loading = False
        if auto_zoom:
            self._debouncer.start()

    def reader_progress_changed(self, progress):
        self.handle_progress_update(progress=progress)

    def reader_max_progress_changed(self, max_progress):
        self.handle_progress_update(max_progress=max_progress)

    def reader_message_changed(self, msg):
        self.handle_progress_update(msg=msg)

    def reader_show_progress_changed(self, show_progress):
        self.handle_progress_update(show_progress=show_progress)

    def _create_message_bar(self):
        message_bar_item = self.iface.messageBar().createMessage("")
        progress_bar = QProgressBar()
        progress_bar.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        cancel_button = QPushButton()
        cancel_button.setText('Cancel')
        cancel_button.clicked.connect(self._cancel_load)
        message_bar_item.layout().addWidget(progress_bar)
        message_bar_item.layout().addWidget(cancel_button)
        self.iface.messageBar().pushWidget(message_bar_item, self.iface.messageBar().INFO)
        self.message_bar_item = message_bar_item
        self.progress_bar = progress_bar

    def handle_progress_update(self, progress=None, max_progress=None, msg=None, show_progress=None):
        if show_progress:
            if not self.message_bar_item:
                self._create_message_bar()
        elif show_progress is False:
            self.iface.messageBar().popWidget(self.message_bar_item)
            self.message_bar_item = None
            self.progress_bar = None
        if max_progress is not None and self.progress_bar:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(max_progress)
        if msg and self.message_bar_item:
            info(msg)
            self.message_bar_item.setTitle(msg)
        if progress is not None and self.progress_bar:
            self.progress_bar.setValue(progress)

    def _assure_qgis_groups_exist(self, root_group_name, sort_layers=False):
        """
         * Createss a group for each layer that is given by the layer source scheme
         >> mbtiles: value 'JSON' in metadata table, array 'vector_layers'
         >> TileJSON: value 'vector_layers'
        :return:
        """

        root = QgsProject.instance().layerTreeRoot()
        root_group = root.findGroup(root_group_name)
        if not root_group:
            root_group = root.addGroup(root_group_name)
        layers = [l["id"] for l in self._current_reader.get_source().vector_layers()]

        if sort_layers:
            layers = sorted(layers, key=lambda n: self._get_omt_layer_sort_id(n))
        for index, layer_name in enumerate(layers):
            group = root_group.findGroup(layer_name)
            if not group:
                root_group.addGroup(layer_name)

    @staticmethod
    def _get_omt_layer_sort_id(layer_name):
        """
         * Returns the cartographic sort id for the specified layer.
         * This sort id is the position of the layer in the omt_layer_ordering collection.
         * If the layer isn't present in the collection, the sort id wil be 999 and therefore the layer will be added at the bottom.
        :param layer_name:
        :return:
        """

        sort_id = 999
        if layer_name in omt_layer_ordering:
            sort_id = omt_layer_ordering.index(layer_name)
        return sort_id

    @staticmethod
    def _add_path_to_dependencies_to_syspath():
        """
         * Adds the path to the external libraries to the sys.path if not already added
        """
        ext_libs_path = os.path.join(get_plugin_directory(), 'ext-libs')
        if ext_libs_path not in sys.path:
            site.addsitedir(ext_libs_path)

    def unload(self):
        if self._current_reader:
            self._current_reader.get_source().close_connection()
            self._current_reader = None

        try:
            self.iface.mapCanvas().xyCoordinates.disconnect(self._handle_mouse_move)
            self.iface.newProjectCreated.disconnect(self._on_project_change)
            self.iface.projectRead.disconnect(self._on_project_change)
            self._debouncer.stop()
            self._debouncer.shutdown()
            self.iface.layerToolBar().removeAction(self.toolButtonAction)
            self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.about_action)
            self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.open_connections_action)
            self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.reload_action)
            self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.clear_cache_action)
            self.iface.addLayerMenu().removeAction(self.open_connections_action)
            logging.shutdown()
        except:
            pass


class SignalDebouncer(QObject):
    """
     * This class can be used to debounce signals, i.e. if many signals are received in a very short timespan,
     only the latest shall be processed and all others ignored.
    """

    on_notify = pyqtSignal(name="onNotify")
    on_notify_in_pause = pyqtSignal(name="onNotifyInPause")

    def __init__(self, timeout, signals, predicate=None):
        QObject.__init__(self)
        self._debounce_timer = QTimer()
        self._debounce_timer.timeout.connect(self._on_timeout)
        self._timeout = timeout
        self._signals = signals
        self._is_connected = False
        self._is_paused = False
        self._is_stopped = False
        self._predicate = predicate

    def start(self):
        """
         * Starts handling the signals
        :return:
        """
        if self._is_paused or self._is_stopped:
            self._is_paused = False
            self._is_stopped = False
        else:
            self._connect()
        self._debounce_timer.start(self._timeout)

    def is_running(self):
        return self._is_connected

    def stop(self):
        """
         * Stops handling the signals
        :return:
        """
        self._is_stopped = True

    def pause(self):
        self._is_paused = True
        self._debounce_timer.stop()
        self._debounce_timer.start(self._timeout)

    def shutdown(self):
        self._disconnect()

    def _connect(self):
        if not self._is_connected:
            for signal in self._signals:
                signal.connect(self._debounce, Qt.QueuedConnection)
            self._is_connected = True

    def _disconnect(self):
        self._debounce_timer.stop()
        if self._is_connected:
            self._is_connected = False
            for s in self._signals:
                s.disconnect(self._debounce)

    def _on_timeout(self):
        self._debounce_timer.stop()
        if self._is_stopped:
            info("Debouncer is stopped")
            return

        should_notify = True
        if self._predicate:
            should_notify = self._predicate()

        if should_notify:
            if self._is_paused:
                self.on_notify_in_pause.emit()
            else:
                self.on_notify.emit()

    def _debounce(self):
        self._debounce_timer.stop()
        if self._is_connected:
            self._debounce_timer.start(self._timeout)
