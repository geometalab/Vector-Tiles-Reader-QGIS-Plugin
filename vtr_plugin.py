# -*- coding: utf-8 -*-

""" THIS COMMENT MUST NOT REMAIN INTACT

GNU GENERAL PUBLIC LICENSE

Copyright (c) 2017 geometalab HSR

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

"""

from log_helper import debug, info, warn, critical
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QAction, QIcon, QMenu, QToolButton,  QMessageBox
from qgis.core import *
from qgis.gui import QgsMessageBar

from file_helper import FileHelper
from tile_helper import get_tile_bounds, epsg3857_to_wgs84_lonlat, tile_to_latlon
from ui.dialogs import AboutDialog, ProgressDialog, ServerConnectionDialog, TilesReloadingDialog

import os
import sys
import site


class VtrPlugin:
    _dialog = None
    _model = None
    add_layer_action = None

    def __init__(self, iface):
        self.iface = iface
        self._add_path_to_dependencies_to_syspath()
        self.settings = QSettings("Vector Tile Reader", "vectortilereader")
        self.server_dialog = ServerConnectionDialog()
        self.server_dialog.on_connect.connect(self._on_connect)
        self.server_dialog.on_add.connect(self._on_add_layer)
        self.progress_dialog = None
        self.reload_dialog = None
        self._current_reader = None
        self._current_options = None
        self.reader = None
        self._connect_to_extent_changed()
        self._add_path_to_icons()

    def _add_path_to_icons(self):
        icons_directory = FileHelper.get_icons_directory()
        current_paths = QgsApplication.svgPaths()
        if icons_directory not in current_paths:
            current_paths.append(icons_directory)
            QgsApplication.setDefaultSvgPaths(current_paths)

    def initGui(self):
        self.popupMenu = QMenu(self.iface.mainWindow())
        self.open_server_action = self._create_action("Add Vector Tiles Layer...", "server.svg", self.server_dialog.show)
        self.iface.insertAddLayerAction(self.open_server_action)  # Add action to the menu: Layer->Add Layer
        self.popupMenu.addAction(self.open_server_action)
        self.toolButton = QToolButton()
        self.toolButton.setMenu(self.popupMenu)
        self.toolButton.setDefaultAction(self.open_server_action)
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButtonAction = self.iface.layerToolBar().addWidget(self.toolButton)
        self.about_action = self._create_action("About", "info.svg", self.show_about)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.about_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.open_server_action)
        info("Vector Tile Reader Plugin loaded...")

    def _connect_to_extent_changed(self):
        self.iface.mapCanvas().extentsChanged.connect(self._on_map_extent_changed)

    def _on_map_extent_changed(self):
        self.iface.mapCanvas().extentsChanged.disconnect()
        is_loading = self.progress_dialog and self.progress_dialog.is_loading()
        if not is_loading and self.reload_dialog:
            should_reload = self.reload_dialog.reload_tiles()
            debug("Reload tiles: {}", should_reload)
            if should_reload:
                reader = self._current_reader
                if reader is not None:
                    scheme = self._current_reader.source.scheme()
                    # todo: replace hardcoded zoom_level 14
                    current_extent = self._get_visible_extent_as_tile_bounds(tilejson_scheme=scheme, zoom=14)
                    self._load_tiles(reader.source.source(), self._current_options, current_extent, reader, override_limit=True)
        self._connect_to_extent_changed()

    def _get_visible_extent_as_tile_bounds(self, tilejson_scheme, zoom):
        e = self.iface.mapCanvas().extent().asWktCoordinates().split(", ")
        new_extent = map(lambda x: map(float, x.split(" ")), e)
        min_extent = new_extent[0]
        max_extent = new_extent[1]

        min_proj = epsg3857_to_wgs84_lonlat(min_extent[0], min_extent[1])
        max_proj = epsg3857_to_wgs84_lonlat(max_extent[0], max_extent[1])

        bounds = []
        bounds.extend(min_proj)
        bounds.extend(max_proj)
        tile = get_tile_bounds(zoom, bounds=bounds, scheme=tilejson_scheme, crs="EPSG:4326")
        return tile

    def _on_connect(self, path_or_url):
        debug("Connect to path_or_url: {}", path_or_url)

        reader = self._create_reader(path_or_url)
        self.reader = reader
        if reader:
            layers = reader.source.vector_layers()
            self.server_dialog.set_layers(layers)
            self.server_dialog.options.set_zoom(reader.source.min_zoom(), reader.source.max_zoom())
        else:
            self.server_dialog.set_layers([])

    def show_about(self):
        AboutDialog().show()

    def _on_add_layer(self, path_or_url, selected_layers):
        print "selected layers: ", selected_layers
        debug("add layer: {}", path_or_url)
        scheme = self.reader.source.scheme()
        crs_string = self.reader.source.crs()
        self._init_qgis_map(crs_string)
        zoom = self.reader.source.max_zoom()
        if zoom is None:
            zoom = 14
        manual_zoom = self.server_dialog.options.manual_zoom()
        if manual_zoom is not None:
            zoom = manual_zoom
        extent = self._get_visible_extent_as_tile_bounds(tilejson_scheme=scheme, zoom=zoom)
        # if not self.tilejson.is_within_bounds(zoom=zoom, extent=extent):
        #     pass  # todo: something's wrong here. probably a CRS mismatch between _get_visible_extent and tilejson
            # print "not in bounds"
            # self._set_qgis_extent(self.tilejson)

        keep_dialog_open = self.server_dialog.keep_dialog_open()
        if keep_dialog_open:
            dialog_owner = self.server_dialog
        else:
            dialog_owner = self.iface.mainWindow()
            self.server_dialog.close()
        self._create_progress_dialog(dialog_owner)
        self._load_tiles(path=path_or_url,
                         options=self.server_dialog.options,
                         layers_to_load=selected_layers,
                         extent_to_load=extent)

    def _set_qgis_extent(self, tilejson):
        """
         * Sets the current extent of the QGIS map canvas to the center of the specified TileJSON
        :param tilejson: 
        :return: 
        """
        center_tile = tilejson.center_tile()
        scheme = tilejson.scheme()
        max_zoom = tilejson.max_zoom()
        center_latlon = tile_to_latlon(max_zoom, center_tile[0], center_tile[1], scheme=scheme)
        map_pos = QgsPoint(center_latlon[0], center_latlon[1])
        rect = QgsRectangle(map_pos, map_pos)
        self.iface.mapCanvas().setExtent(rect)

    def _init_qgis_map(self, crs_string):
        crs = QgsCoordinateReferenceSystem(crs_string)
        if not crs.isValid():
            crs = QgsCoordinateReferenceSystem("EPSG:3857")
        self.iface.mapCanvas().mapRenderer().setDestinationCrs(crs)

    def _create_progress_dialog(self, owner):
        self.progress_dialog = ProgressDialog(owner)
        self.progress_dialog.on_cancel.connect(self._cancel_load)

    def _cancel_load(self):
        if self._current_reader:
            self._current_reader.cancel()

    def _create_action(self, title, icon, callback):
        new_action = QAction(QIcon(':/plugins/vectortilereader/{}'.format(icon)), title, self.iface.mainWindow())
        new_action.triggered.connect(callback)
        return new_action

    def _load_tiles(self, path, options, layers_to_load, extent_to_load=None, reader=None, override_limit=False):
        merge_tiles = options.merge_tiles_enabled()
        apply_styles = options.apply_styles_enabled()
        tile_limit = options.tile_number_limit()
        if override_limit:
            tile_limit = None
        manual_zoom = options.manual_zoom()
        cartographic_ordering = options.cartographic_ordering()

        debug("Load: {}", path)
        if not reader:
            reader = self._create_reader(path)
            self._current_reader = reader
            self._current_options = options
            if options.auto_load_tiles():
                self.reload_dialog = TilesReloadingDialog()
            else:
                self.reload_dialog = None
        if reader:
            reader.enable_cartographic_ordering(enabled=cartographic_ordering)
            try:
                zoom = reader.source.max_zoom()
                if manual_zoom is not None:
                    zoom = manual_zoom
                reader.load_tiles(zoom_level=zoom,
                                  layer_filter=layers_to_load,
                                  load_mask_layer=False,
                                  merge_tiles=merge_tiles,
                                  apply_styles=apply_styles,
                                  max_tiles=tile_limit,
                                  extent_to_load=extent_to_load,
                                  limit_reacher_handler=lambda: self._show_limit_exceeded_message(tile_limit))
                self.refresh_layers()
                debug("Loading complete!")
            except RuntimeError:
                self._current_reader = None
                QMessageBox.critical(None, "Unexpected exception", str(sys.exc_info()[1]))
                critical(str(sys.exc_info()[1]))

    def refresh_layers(self):
        for layer in self.iface.mapCanvas().layers():
            layer.triggerRepaint()

    def _show_limit_exceeded_message(self, limit):
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
            reader = VtReader(self.iface,
                              path_or_url=path_or_url,
                              progress_handler=self.handle_progress_update)
        except RuntimeError:
            QMessageBox.critical(None, "Loading Error", str(sys.exc_info()[1]))
            critical(str(sys.exc_info()[1]))
        return reader

    def handle_progress_update(self, title, progress, max_progress, msg, show_progress):
        if show_progress:
            self.progress_dialog.open()
        elif show_progress is False:
            self.progress_dialog.hide()
            self.progress_dialog.set_message(None)
        if title:
            self.progress_dialog.setWindowTitle(title)
        if max_progress:
            self.progress_dialog.set_maximum(max_progress)
        if msg:
            self.progress_dialog.set_message(msg)
        if progress:
            self.progress_dialog.set_progress(progress)

    def _add_path_to_dependencies_to_syspath(self):
        """
         * Adds the path to the external libraries to the sys.path if not already added
        """
        ext_libs_path = os.path.abspath(os.path.dirname(__file__) + '/ext-libs')
        if ext_libs_path not in sys.path:
            site.addsitedir(ext_libs_path)

    def unload(self):
        try:
            self.iface.mapCanvas().extentsChanged.disconnect()
        except:
            warn("Disconnectin failed: {}", sys.exc_info())
        self.iface.layerToolBar().removeAction(self.toolButtonAction)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.about_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.open_server_action)
        self.iface.addLayerMenu().removeAction(self.open_server_action)
