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

from file_helper import FileHelper
from tile_helper import get_tile_bounds, epsg3857_to_wgs84_lonlat, tile_to_latlon
from tile_json import TileJSON
from ui.dialogs import FileConnectionDialog, AboutDialog, ProgressDialog, ServerConnectionDialog, TilesReloadingDialog

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
        self.file_dialog = FileConnectionDialog(FileHelper.get_home_directory())
        self.file_dialog.on_open.connect(self._on_open_mbtiles)
        self.file_dialog.on_valid_file_path_changed.connect(self._update_zoom_from_file)
        self.server_dialog = ServerConnectionDialog()
        self.server_dialog.on_connect.connect(self._on_connect)
        self.server_dialog.on_add.connect(self._on_add_server_layer)
        self.progress_dialog = None
        self.reload_dialog = None
        self._current_reader = None
        self._current_options = None
        self.iface.mapCanvas().extentsChanged.connect(self._on_map_extent_changed)

    def initGui(self):
        self.add_layer_action = self._create_action("Add Vector Tiles Layer...", "icon.png", self.run)
        self.about_action = self._create_action("About", "", self.show_about)
        self.iface.addPluginToMenu("&Vector Tiles Reader", self.about_action)
        self.iface.insertAddLayerAction(self.add_layer_action)  # Add action to the menu: Layer->Add Layer
        self.add_menu()
        info("Vector Tile Reader Plugin loaded...")

    def _on_map_extent_changed(self):
        pass
        # is_loading = self.progress_dialog and self.progress_dialog.is_loading()
        # if not is_loading and self.reload_dialog:
        #     should_reload = self.reload_dialog.reload_tiles()
        #     debug("Reload tiles: {}", should_reload)
        # reader = self._current_reader
        # if reader is not None:
        #     scheme = self._current_reader.source.scheme()
        #     current_extent = self._get_visible_extent_as_tile_bounds(scheme)
        #     self._load_tiles(reader.source.source(), self._current_options, current_extent, reader)

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
        tile = get_tile_bounds(zoom, bounds=bounds, scheme=tilejson_scheme)
        return tile

    def _on_connect(self, url):
        debug("Connect to url: {}", url)
        self.url = url
        tilejson = TileJSON(url)
        if tilejson.load():
            layers = tilejson.vector_layers()
            self.server_dialog.set_layers(layers)
            self.server_dialog.options.set_zoom(tilejson.min_zoom(), tilejson.max_zoom())
        else:
            self.server_dialog.set_layers([])
            tilejson = None
        self.tilejson = tilejson

    def _update_zoom_from_file(self, path):
        min_zoom = None
        max_zoom = None
        reader = self._create_reader(path)
        if reader:
            min_zoom = reader.source.min_zoom()
            max_zoom = reader.source.max_zoom()
        else:
            self.file_dialog.clear_path()
        self.file_dialog.options.set_zoom(min_zoom, max_zoom)

    def show_about(self):
        AboutDialog().show()

    def add_menu(self):
        self.popupMenu = QMenu(self.iface.mainWindow())
        open_file_action = self._create_action("Add Vector Tile Layer...", "icon.png", self.file_dialog.show)
        open_server_action = self._create_action("Add Vector Tile Server Layer...", "server.svg", self.server_dialog.show)
        self.popupMenu.addAction(self._create_action("Add Vector Tile Layer...", "folder.svg", self.file_dialog.show))
        self.popupMenu.addAction(open_server_action)
        self.toolButton = QToolButton()
        self.toolButton.setMenu(self.popupMenu)
        self.toolButton.setDefaultAction(open_file_action)
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButtonAction = self.iface.layerToolBar().addWidget(self.toolButton)

    def _on_add_server_layer(self, url):
        debug("add server layer: {}", url)
        assert self.tilejson
        scheme = self.tilejson.scheme()
        crs_string = self.tilejson.crs()
        self._init_qgis_map(crs_string)
        max_zoom = self.tilejson.max_zoom()
        if not max_zoom:
            max_zoom = 14
        extent = self._get_visible_extent_as_tile_bounds(tilejson_scheme=scheme, zoom=max_zoom)
        if not self.tilejson.is_within_bounds(zoom=max_zoom, extent=extent):
            self._set_qgis_extent(self.tilejson)

        keep_dialog_open = self.server_dialog.keep_dialog_open()
        if keep_dialog_open:
            dialog_owner = self.server_dialog
        else:
            dialog_owner = self.iface.mainWindow()
            self.server_dialog.close()
        self._create_progress_dialog(dialog_owner)
        self._load_tiles(path=url, options=self.server_dialog.options, extent_to_load=extent)

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

    def _on_open_mbtiles(self, path):
        self._create_progress_dialog(self.iface.mainWindow())
        self._load_tiles(path=path, options=self.file_dialog.options, extent_to_load=None)

    def _create_action(self, title, icon, callback):
        new_action = QAction(QIcon(':/plugins/vectortilereader/{}'.format(icon)), title, self.iface.mainWindow())
        new_action.triggered.connect(callback)
        return new_action

    def _load_tiles(self, path, options, extent_to_load=None, reader=None):
        merge_tiles = options.merge_tiles_enabled()
        apply_styles = options.apply_styles_enabled()
        tile_limit = options.tile_number_limit()
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
                                  load_mask_layer=False,
                                  merge_tiles=merge_tiles,
                                  apply_styles=apply_styles,
                                  max_tiles=tile_limit,
                                  extent_to_load=extent_to_load)
                self.refresh_layers()
                debug("Loading complete!")
            except RuntimeError:
                self._current_reader = None
                QMessageBox.critical(None, "Unexpected exception", str(sys.exc_info()[1]))
                critical(str(sys.exc_info()[1]))

    def refresh_layers(self):
        for layer in self.iface.mapCanvas().layers():
            layer.triggerRepaint()

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
        self.iface.layerToolBar().removeAction(self.toolButtonAction)
        self.iface.removePluginMenu("&Vector Tiles Reader", self.about_action)
        self.iface.addLayerMenu().removeAction(self.add_layer_action)

    def run(self):
        self.file_dialog.show()
