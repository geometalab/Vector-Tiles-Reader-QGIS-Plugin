# -*- coding: utf-8 -*-

""" THIS COMMENT MUST NOT REMAIN INTACT

GNU GENERAL PUBLIC LICENSE

Copyright (c) 2017 geometalab HSR

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

"""

from builtins import map
from builtins import str
from builtins import object
from log_helper import info, critical
from PyQt4.QtCore import QSettings, QTimer, Qt, pyqtSlot, pyqtSignal, QObject
from PyQt4.QtGui import (
    QAction,
    QIcon,
    QMenu,
    QToolButton,
    QMessageBox,
    QColor,
    QFileDialog,
    QProgressBar,
    QPushButton)
from qgis.core import *
from qgis.gui import QgsMessageBar

from file_helper import (get_icons_directory,
                         get_home_directory,
                         get_sample_data_directory,
                         clear_cache,
                         get_plugin_directory,
                         paths_equal)
from tile_helper import *
from ui.dialogs import AboutDialog, ProgressDialog, ConnectionsDialog

import os
import sys
import site
import traceback
import re

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


class VtrPlugin(object):
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
        self._add_path_to_dependencies_to_syspath()
        self.settings = QSettings("Vector Tile Reader", "vectortilereader")
        self._clear_cache_when_version_changed()
        self.connections_dialog = ConnectionsDialog(self._get_initial_browse_directory())
        self.connections_dialog.on_connect.connect(self._on_connect)
        self.connections_dialog.on_add.connect(self._on_add_layer)
        self.connections_dialog.on_zoom_change.connect(self._update_nr_of_tiles)
        self.progress_dialog = None
        self._current_reader = None
        self._current_writer = None
        self._current_options = None
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
                                          signals=[self.iface.mapCanvas().scaleChanged,
                                                   self.iface.mapCanvas().extentsChanged],
                                          predicate=self._have_extent_or_scale_changed)
        self._debouncer.on_notify.connect(self._handle_map_scale_or_extents_changed)
        self._debouncer.on_notify_in_pause.connect(self._on_scale_or_extent_change_during_pause)
        self._scale_to_load = None
        self._extent_to_load = None
        self.message_bar_item = None
        self.progress_bar = None

    @staticmethod
    def _get_initial_browse_directory():
        """
         * If qgis is started in a specific folder, this folder will be used as initial directory when browsing sources
          Otherwise, the sample data folder will be opened.
        :return:
        """

        qgis_path = QgsApplication.pkgDataPath().replace("/apps/qgis", "/bin")
        open_path = get_sample_data_directory()
        cwd = os.getcwd()
        if not paths_equal(cwd, qgis_path):
            open_path = cwd
        return open_path

    def _clear_cache_when_version_changed(self):
        latest_version = self._get_plugin_version()
        local_version = self.settings.value("vectortilereader/version", None)
        if not local_version or local_version != latest_version:
            clear_cache()
        self.settings.setValue("vectortilereader/version", latest_version)

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
        self._debouncer.stop()
        self._cancel_export()
        self._cancel_load()
        self.connections_dialog.set_layers([])
        if self._current_reader:
            self._current_reader.shutdown()
            self._current_reader = None

    def initGui(self):
        self.popupMenu = QMenu(self.iface.mainWindow())
        self.open_connections_action = self._create_action("Add Vector Tiles Layer...", "server.svg",
                                                           self._show_connections_dialog)
        self.reload_action = self._create_action(self._reload_button_text, "reload.svg", self._reload_tiles, False)
        self.export_action = self._create_action("Export selected layers", "save.svg", self._export_tiles)
        self.clear_cache_action = self._create_action("Clear cache", "delete.svg", clear_cache)
        self.about_action = self._create_action("About", "info.svg", self.show_about)
        self.iface.insertAddLayerAction(self.open_connections_action)  # Add action to the menu: Layer->Add Layer
        self.popupMenu.addAction(self.open_connections_action)
        self.popupMenu.addAction(self.reload_action)
        self.popupMenu.addAction(self.export_action)
        self.popupMenu.addAction(self.clear_cache_action)
        self.popupMenu.addAction(self.about_action)
        self.toolButton = QToolButton()
        self.toolButton.setMenu(self.popupMenu)
        self.toolButton.setDefaultAction(self.open_connections_action)
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButtonAction = self.iface.layerToolBar().addWidget(self.toolButton)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.open_connections_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.reload_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.export_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.clear_cache_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.about_action)
        info("Vector Tile Reader Plugin loaded...")

    def _have_extent_or_scale_changed(self):
        has_scale_changed = self._has_scale_changed()[0]
        has_extent_changed = self._has_extent_changed()[0]
        return has_scale_changed or has_extent_changed

    @pyqtSlot()
    def _on_scale_or_extent_change_during_pause(self):
        assert self._current_reader
        self._scale_to_load = None
        self._extent_to_load = None

        info("got request in pause")
        has_scale_changed, new_target_scale, has_scale_increased = self._has_scale_changed()
        if has_scale_changed:
            self._scale_to_load = None
        else:
            has_extent_changed, new_target_extent = self._has_extent_changed()
            if has_extent_changed:
                self._extent_to_load = new_target_extent

        if self._is_loading and (self._scale_to_load or self._extent_to_load):
            self._cancel_load()

    def _has_extent_changed(self):
        scheme = self._current_reader.source.scheme()
        scale = self._scale_to_load
        if not scale:
            scale = self._get_current_map_scale()

        if self._extent_to_load:
            new_extent = self._extent_to_load
        else:
            zoom = get_zoom_by_scale(scale)
            max_zoom = self._current_reader.source.max_zoom()
            min_zoom = self._current_reader.source.min_zoom()
            zoom = clamp(zoom, low=min_zoom, high=max_zoom)
            new_extent = self._get_visible_extent_as_tile_bounds(scheme, zoom)
        has_changed = new_extent != self._loaded_extent
        return has_changed, new_extent

    def _has_scale_changed(self):
        new_scale = self._get_current_map_scale()
        if self._scale_to_load:
            new_scale = self._scale_to_load

        has_changed = new_scale != self._loaded_scale
        scale_increased = self._current_scale is None or new_scale > self._current_scale
        return has_changed, new_scale, scale_increased

    @pyqtSlot()
    def _handle_map_scale_or_extents_changed(self):
        if not self._is_loading and self._current_reader and self.connections_dialog.options.auto_zoom_enabled():
            has_scale_changed, new_scale, has_scale_increased = self._has_scale_changed()
            has_extent_changed, new_extent = self._has_extent_changed()

            self._scale_to_load = None
            self._extent_to_load = None
            
            is_new_extent_within_loaded_extent = self._loaded_extent \
                and self._loaded_extent["x_min"] <= new_extent["x_min"] <= self._loaded_extent["x_max"] \
                and self._loaded_extent["x_min"] <= new_extent["x_max"] <= self._loaded_extent["x_max"] \
                and self._loaded_extent["y_min"] <= new_extent["y_min"] <= self._loaded_extent["y_max"] \
                and self._loaded_extent["y_min"] <= new_extent["y_max"] <= self._loaded_extent["y_max"]

            old_scale = self._loaded_scale

            new_zoom = self._get_zoom_for_current_map_scale()
            min_zoom = self._current_reader.source.min_zoom()
            max_zoom = self._current_reader.source.max_zoom()
            new_zoom = clamp(new_zoom, low=min_zoom, high=max_zoom)

            has_zoom_changed = new_zoom != self._current_zoom
            if new_scale and has_scale_changed and has_zoom_changed:
                self._loaded_scale = new_scale
                self._loaded_extent = new_extent

                info("current zoom: {}", self._current_zoom)
                info("new zoom: {}", new_zoom)
                info("Reloading due to scale change from '{}' (zoom {}) to '{}' (zoom {})", old_scale, self._current_zoom, new_scale, new_zoom)
                self._handle_scale_change(new_scale)
            elif has_extent_changed and not is_new_extent_within_loaded_extent:
                self._loaded_scale = new_scale
                self._loaded_extent = new_extent

                info("Reloading due to extent change from '{}' to '{}'", self._loaded_extent, new_extent)
                self._loaded_extent = new_extent
                self._reload_tiles(new_extent)

    def _handle_scale_change(self, new_scale):
        scale_increased = self._current_scale is None or new_scale > self._current_scale
        self._current_scale = new_scale
        max_zoom = self._current_reader.source.max_zoom()
        new_zoom = get_zoom_by_scale(new_scale)
        if new_zoom > max_zoom:
            new_zoom = max_zoom
        current_zoom = self._current_zoom
        if new_zoom != current_zoom or (scale_increased and new_scale > self._loaded_scale):
            self._loaded_scale = new_scale
            self._reload_tiles()
            self.iface.mapCanvas().zoomScale(new_scale)

    def _handle_mouse_move(self, pos):
        self.iface.mapCanvas().xyCoordinates.disconnect(self._handle_mouse_move)
        zoom = self._get_current_zoom()
        lat_lon = epsg3857_to_wgs84_lonlat(pos[1], pos[0])
        tile = latlon_to_tile(zoom, lat_lon[0], lat_lon[1])
        msg = "ZXY: {}, {}, {}".format(zoom, tile[0], tile[1])
        self.iface.mainWindow().statusBar().showMessage(msg)
        self.iface.mapCanvas().xyCoordinates.connect(self._handle_mouse_move)

    @staticmethod
    def _add_path_to_icons():
        icons_directory = get_icons_directory()
        current_paths = QgsApplication.svgPaths()
        if icons_directory not in current_paths:
            current_paths.append(icons_directory)
            QgsApplication.setDefaultSvgPaths(current_paths)

    @pyqtSlot()
    def _update_nr_of_tiles(self):
        zoom = self._get_current_zoom()
        bounds = self._get_visible_extent_as_tile_bounds(scheme="xyz", zoom=zoom)
        nr_of_tiles = bounds["width"] * bounds["height"]
        self.connections_dialog.set_nr_of_tiles(nr_of_tiles)

        map_scale_zoom = self._get_zoom_for_current_map_scale()
        if self._current_reader:
            min_zoom = self._current_reader.source.min_zoom()
            max_zoom = self._current_reader.source.max_zoom()
            map_scale_zoom = clamp(map_scale_zoom, low=min_zoom, high=max_zoom)
        self.connections_dialog.set_current_zoom_level(map_scale_zoom)

    def _show_connections_dialog(self):
        self._update_nr_of_tiles()
        self.connections_dialog.show()

    def _export_tiles(self):
        from vt_writer import VtWriter
        file_name = QFileDialog.getSaveFileName(None, "Export Vector Tiles", get_home_directory(), "mbtiles (*.mbtiles)")
        if file_name:
            self.export_action.setDisabled(True)
            try:
                self._current_writer = VtWriter(self.iface, file_name, progress_handler=self.handle_progress_update)
                self._create_progress_dialog(self.iface.mainWindow(), on_cancel=self._cancel_export)
                self._current_writer.export()
            except:
                critical("Error during export: {}", sys.exc_info())
            self.export_action.setEnabled(True)

    def _get_all_own_layers(self):
        layers = []
        for l in list(QgsMapLayerRegistry.instance().mapLayers().values()):
            data_url = l.dataUrl().lower()
            if data_url and self._current_reader.source.source().lower().startswith(data_url):
                layers.append(l)
        return layers

    def _reload_tiles(self, overwrite_extent=None):
        if self._debouncer.is_running():
            self._debouncer.pause()
        if self._current_reader:
            # self._create_progress_dialog(self.iface.mainWindow(), on_cancel=self._cancel_load)
            scheme = self._current_reader.source.scheme()
            zoom = self._get_current_zoom()
            auto_zoom_enabled = self.connections_dialog.options.auto_zoom_enabled()
            flush_loaded_layers = auto_zoom_enabled and zoom != self._current_zoom
            self._current_zoom = zoom
            if flush_loaded_layers:
                self._current_reader.flush_layers_of_other_zoom_level = True

            bounds = self._get_visible_extent_as_tile_bounds(scheme=scheme, zoom=zoom)
            if overwrite_extent:
                bounds = overwrite_extent

            if self.connections_dialog.options.auto_zoom_enabled():
                self._current_reader.always_overwrite_geojson(True)
            self._load_tiles(options=self.connections_dialog.options,
                             layers_to_load=self._current_layer_filter,
                             bounds=bounds,
                             ignore_limit=True)

    def _get_current_extent_as_wkt(self):
        return self.iface.mapCanvas().extent().asWktCoordinates()

    def _get_visible_extent_as_tile_bounds(self, scheme, zoom):
        extent = self._get_current_extent_as_wkt()
        splits = extent.split(", ")
        new_extent = [list(map(float, x.split(" "))) for x in splits]
        min_extent = new_extent[0]
        max_extent = new_extent[1]

        min_proj = epsg3857_to_wgs84_lonlat(min_extent[0], min_extent[1])
        max_proj = epsg3857_to_wgs84_lonlat(max_extent[0], max_extent[1])

        bounds = []
        bounds.extend(min_proj)
        bounds.extend(max_proj)
        tile_bounds = get_tile_bounds(zoom, bounds=bounds, scheme=scheme)

        debug("Current extent: {}", tile_bounds)
        return tile_bounds

    @pyqtSlot('QString', 'QString')
    def _on_connect(self, connection_name, path_or_url):
        self._currrent_connection_name = connection_name
        debug("Connect to path_or_url: {}", path_or_url)
        self.reload_action.setText("{} ({})".format(self._reload_button_text, connection_name))
        try:
            if self._current_reader and self._current_reader.source.source() != path_or_url:
                self._current_reader.shutdown()
                self._current_reader.progress_changed.disconnect()
                self._current_reader.max_progress_changed.disconnect()
                self._current_reader.title_changed.disconnect()
                self._current_reader.message_changed.disconnect()
                self._current_reader.show_progress_changed.disconnect()
                self._current_reader = None
            if not self._current_reader:
                reader = self._create_reader(path_or_url)
                self._current_reader = reader
            if self._current_reader:
                layers = self._current_reader.source.vector_layers()
                self.connections_dialog.set_layers(layers)
                self.connections_dialog.options.set_zoom(self._current_reader.source.min_zoom(), self._current_reader.source.max_zoom())
                self.reload_action.setEnabled(True)
            else:
                self.connections_dialog.set_layers([])
                self.reload_action.setEnabled(False)
                self.reload_action.setText(self._reload_button_text)
        except:
            QMessageBox.critical(None, "Unexpected Error", "An unexpected error occured. {}".format(str(sys.exc_info()[1])))

    @staticmethod
    def show_about():
        AboutDialog().show()

    def _is_valid_qgis_extent(self, extent_to_load, zoom):
        source_bounds = self._current_reader.source.bounds_tile(zoom)
        info("bounds: {}", source_bounds)
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

    @pyqtSlot('QString', 'QString', list)
    def _on_add_layer(self, connection_name, path_or_url, selected_layers):
        assert path_or_url
        self._assure_qgis_groups_exist(connection_name, True)

        crs_string = self._current_reader.source.crs()
        self._init_qgis_map(crs_string)

        scheme = self._current_reader.source.scheme()
        zoom = self._get_current_zoom()

        extent = self._get_visible_extent_as_tile_bounds(scheme=scheme, zoom=zoom)

        bounds = self._current_reader.source.bounds_tile(zoom)
        info("Bounds of source: {}", bounds)
        is_within_bounds = self.is_extent_within_bounds(extent, bounds)
        if not is_within_bounds:
            # todo: set the current QGIS map extent inside the available bounds of the source
            pass

        if not self._is_valid_qgis_extent(extent_to_load=extent, zoom=zoom):
            extent = self._current_reader.source.bounds_tile(zoom)

        keep_dialog_open = self.connections_dialog.keep_dialog_open()
        if keep_dialog_open:
            dialog_owner = self.connections_dialog
        else:
            dialog_owner = self.iface.mainWindow()
            self.connections_dialog.close()
        self._create_progress_dialog(dialog_owner, on_cancel=self._cancel_load)
        self._load_tiles(options=self.connections_dialog.options,
                         layers_to_load=selected_layers,
                         bounds=extent)
        self._current_layer_filter = selected_layers

    def _get_current_zoom(self):
        zoom = 14
        if self._current_reader:
            zoom = self._current_reader.source.max_zoom()
        if zoom is None:
            zoom = 14
        manual_zoom = self.connections_dialog.options.manual_zoom()
        if manual_zoom is not None:
            zoom = manual_zoom
        if self.connections_dialog.options.auto_zoom_enabled():
            scale_based_zoom = self._get_zoom_for_current_map_scale()
            if scale_based_zoom > zoom:
                scale_based_zoom = zoom
            zoom = scale_based_zoom
        return zoom

    def _set_qgis_extent(self, zoom, scheme, bounds):
        """
         * Sets the current extent of the QGIS map canvas to the specified bounds
        :return: 
        """
        min_pos = tile_to_latlon(zoom, bounds["x_min"], bounds["y_min"], scheme=scheme)
        max_pos = tile_to_latlon(zoom, bounds["x_max"], bounds["y_max"], scheme=scheme)
        map_min_pos = QgsPoint(min_pos[0], min_pos[1])
        map_max_pos = QgsPoint(max_pos[0], max_pos[1])
        rect = QgsRectangle(map_min_pos, map_max_pos)
        self.iface.mapCanvas().setExtent(rect)
        self.iface.mapCanvas().refresh()

    def _init_qgis_map(self, crs_string):
        crs = QgsCoordinateReferenceSystem(crs_string)
        if not crs.isValid():
            crs = QgsCoordinateReferenceSystem("EPSG:3857")
        self.iface.mapCanvas().mapRenderer().setDestinationCrs(crs)

    def _create_progress_dialog(self, owner, on_cancel):
        self.progress_dialog = ProgressDialog(owner)
        if on_cancel:
            self.progress_dialog.on_cancel.connect(on_cancel)

    def _cancel_load(self):
        if self._current_reader:
            self._current_reader.cancel()

    def _cancel_export(self):
        if self._current_writer:
            self._current_writer.cancel()

    def _create_action(self, title, icon, callback, is_enabled=True):
        new_action = QAction(QIcon(':/plugins/vector_tiles_reader/{}'.format(icon)), title, self.iface.mainWindow())
        new_action.triggered.connect(callback)
        new_action.setEnabled(is_enabled)
        return new_action

    def _extent_overlap_bounds(self, extent, bounds):
        return (bounds["x_min"] <= extent["x_min"] <= bounds["x_max"] or
                bounds["x_min"] <= extent["x_max"] <= bounds["x_max"]) and\
                (bounds["y_min"] <= extent["y_min"] <= bounds["y_max"] or
                 bounds["y_min"] <= extent["y_max"] <= bounds["y_max"])

    def _load_tiles(self, options, layers_to_load, bounds=None, ignore_limit=False):
        if self._debouncer.is_running():
            self._debouncer.pause()

        merge_tiles = options.merge_tiles_enabled()
        apply_styles = options.apply_styles_enabled()
        tile_limit = options.tile_number_limit()
        load_mask_layer = options.load_mask_layer_enabled()
        self._auto_zoom = options.auto_zoom_enabled()
        if ignore_limit:
            tile_limit = None
        manual_zoom = options.manual_zoom()
        clip_tiles = options.clip_tiles()

        if apply_styles:
            self._set_background_color()

        reader = self._current_reader
        if not reader:
            self._is_loading = False
        else:
            try:
                max_zoom = reader.source.max_zoom()
                min_zoom = reader.source.min_zoom()
                if self._auto_zoom:
                    zoom = self._get_zoom_for_current_map_scale()
                    zoom = clamp(zoom, low=min_zoom, high=max_zoom)
                else:
                    zoom = max_zoom
                    if manual_zoom is not None:
                        zoom = manual_zoom
                self._current_zoom = zoom

                source_bounds = reader.source.bounds_tile(zoom)
                if source_bounds and not self._extent_overlap_bounds(bounds, source_bounds):
                    info("The current extent '{}' is not within the bounds of the source '{}'. The extent to load "
                         "will be set to the bounds of the source", bounds, source_bounds)
                    bounds = source_bounds

                reader.set_options(layer_filter=layers_to_load,
                                   load_mask_layer=load_mask_layer,
                                   merge_tiles=merge_tiles,
                                   clip_tiles=clip_tiles,
                                   apply_styles=apply_styles,
                                   max_tiles=tile_limit)
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
                if self.progress_dialog:
                    self.progress_dialog.hide()
                self._is_loading = False

    def _set_background_color(self):
        myColor = QColor("#F2EFE9")
        # Write it to the project (will still need to be saved!)
        QgsProject.instance().writeEntry("Gui", "/CanvasColorRedPart", myColor.red())
        QgsProject.instance().writeEntry("Gui", "/CanvasColorGreenPart", myColor.green())
        QgsProject.instance().writeEntry("Gui", "/CanvasColorBluePart", myColor.blue())
        # And apply for the current session
        self.iface.mapCanvas().setCanvasColor(myColor)
        self.iface.mapCanvas().refresh()

    def refresh_layers(self):
        for layer in self.iface.mapCanvas().layers():
            layer.triggerRepaint()

    @pyqtSlot()
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
                self._debouncer.start(start_immediate=True)

    @pyqtSlot(int)
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

    def _create_reader(self, path_or_url):
        # A lazy import is required because the vtreader depends on the external libs
        from vt_reader import VtReader
        reader = None
        try:
            reader = VtReader(self.iface, path_or_url=path_or_url)
            reader.progress_changed.connect(self.reader_progress_changed)
            reader.max_progress_changed.connect(self.reader_max_progress_changed)
            reader.show_progress_changed.connect(self.reader_show_progress_changed)
            reader.title_changed.connect(self.reader_title_changed)
            reader.message_changed.connect(self.reader_message_changed)
            reader.loading_finished.connect(self.reader_loading_finished)
            reader.tile_limit_reached.connect(self.reader_limit_exceeded_message)
            reader.cancelled.connect(self.reader_cancelled)
            reader.add_layer_to_group.connect(self.add_layer_to_group)
        except RuntimeError:
            QMessageBox.critical(None, "Loading Error", str(sys.exc_info()[1]))
            critical(str(sys.exc_info()[1]))
        return reader

    @pyqtSlot(list)
    def add_layers(self, layers):
        info("add layers: {}", layers)
        QgsMapLayerRegistry.instance().addMapLayers(layers, False)

    @pyqtSlot('QString', object)
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

    @pyqtSlot(object)
    def reader_loading_finished(self, loaded_zoom_level, loaded_extent):
        self._loaded_extent = loaded_extent
        self.handle_progress_update(show_progress=False)
        # if self.progress_dialog:
        #     self.progress_dialog.hide()

        auto_zoom = self._auto_zoom

        self._loaded_scale = self._get_current_map_scale()
        self.refresh_layers()
        info("Loading of zoom level {} complete! Loaded extent: {}", loaded_zoom_level, loaded_extent)
        if loaded_extent and (not auto_zoom or (auto_zoom and self._loaded_scale is None)):
            scheme = self._current_reader.source.scheme()
            visible_extent = self._get_visible_extent_as_tile_bounds(scheme, loaded_zoom_level)
            overlap = self._extent_overlap_bounds(visible_extent, loaded_extent)
            if not overlap:
                self._set_qgis_extent(zoom=loaded_zoom_level, scheme=scheme, bounds=loaded_extent)

        self._is_loading = False
        if auto_zoom:
            self._debouncer.start()

    @pyqtSlot(int)
    def reader_progress_changed(self, progress):
        self.handle_progress_update(progress=progress)

    @pyqtSlot(int)
    def reader_max_progress_changed(self, max_progress):
        self.handle_progress_update(max_progress=max_progress)

    @pyqtSlot('QString')
    def reader_title_changed(self, title):
        self.handle_progress_update(title=title)

    @pyqtSlot('QString')
    def reader_message_changed(self, msg):
        self.handle_progress_update(msg=msg)

    @pyqtSlot(bool)
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

    def handle_progress_update(self, title=None, progress=None, max_progress=None, msg=None, show_progress=None):
        if show_progress:
            if not self.message_bar_item:
                self._create_message_bar()
            # self.progress_dialog.open()
        elif show_progress is False:
            info("hide progress")
            self.iface.messageBar().popWidget(self.message_bar_item)
            self.message_bar_item = None
            self.progress_bar = None
            # self.progress_dialog.hide()
            # self.progress_dialog.set_message(None)
        if title:
            pass
            # self.message_bar_item.setTitle(title)
            # self.progress_dialog.setWindowTitle(title)
        if max_progress is not None:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(max_progress)
            # self.progress_dialog.set_maximum(max_progress)
        if msg:
            info(msg)
            self.message_bar_item.setTitle(msg)
            # self.progress_dialog.set_message(msg)
        if progress is not None:
            self.progress_bar.setValue(progress)
            # self.progress_dialog.set_progress(progress)

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
        layers = [l["id"] for l in self._current_reader.source.vector_layers()]

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
        ext_libs_path = os.path.abspath(os.path.dirname(__file__) + '/ext-libs')
        if ext_libs_path not in sys.path:
            site.addsitedir(ext_libs_path)

    def unload(self):
        if self._current_reader:
            self._current_reader.source.close_connection()
            self._current_reader = None
        try:
            self._disconnect_map_scale_changed()
        except:
            pass

        self.iface.newProjectCreated.disconnect(self._on_project_change)
        self.iface.projectRead.disconnect(self._on_project_change)
        self._debouncer.stop()
        self.iface.layerToolBar().removeAction(self.toolButtonAction)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.about_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.open_connections_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.reload_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.export_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.clear_cache_action)
        self.iface.addLayerMenu().removeAction(self.open_connections_action)
        try:
            self.iface.mapCanvas().xyCoordinates.disconnect(self._handle_mouse_move)
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
        self._predicate = predicate

    def start(self, start_immediate=False):
        """
         * Starts handling the signals
        :return:
        """
        if self._is_paused:
            self._is_paused = False
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
        self._disconnect()

    def pause(self):
        self._is_paused = True
        self._debounce_timer.stop()
        self._debounce_timer.start(self._timeout)

    def _connect(self):
        if not self._is_connected:
            for s in self._signals:
                s.connect(self._debounce, Qt.QueuedConnection)
            self._is_connected = True

    def _disconnect(self):
        self._debounce_timer.stop()
        if self._is_connected:
            self._is_connected = False
            for s in self._signals:
                s.disconnect(self._debounce)

    @pyqtSlot()
    def _on_timeout(self):
        self._debounce_timer.stop()

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
