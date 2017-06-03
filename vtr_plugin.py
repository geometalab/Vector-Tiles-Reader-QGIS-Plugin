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
from PyQt4.QtGui import QAction, QIcon, QMenu, QToolButton,  QMessageBox, QColor, QFileDialog
from qgis.core import *
from qgis.gui import QgsMessageBar

from file_helper import FileHelper
from tile_helper import get_tile_bounds, epsg3857_to_wgs84_lonlat, tile_to_latlon, convert_coordinate
from ui.dialogs import AboutDialog, ProgressDialog, ConnectionsDialog

import os
import sys
import site


class VtrPlugin:
    _dialog = None
    _model = None
    _reload_button_text = "Load features overlapping the view extent"
    add_layer_action = None

    def __init__(self, iface):
        self.iface = iface
        self._add_path_to_dependencies_to_syspath()
        self.settings = QSettings("Vector Tile Reader", "vectortilereader")
        self.connections_dialog = ConnectionsDialog(FileHelper.get_sample_data_directory())
        self.connections_dialog.on_connect.connect(self._on_connect)
        self.connections_dialog.on_add.connect(self._on_add_layer)
        self.connections_dialog.on_zoom_change.connect(self._update_nr_of_tiles)
        self.progress_dialog = None
        self._current_reader = None
        self._current_options = None
        self.reader = None
        self._add_path_to_icons()
        self._current_source_path = None
        self._current_layer_filter = []

    def _add_path_to_icons(self):
        icons_directory = FileHelper.get_icons_directory()
        current_paths = QgsApplication.svgPaths()
        if icons_directory not in current_paths:
            current_paths.append(icons_directory)
            QgsApplication.setDefaultSvgPaths(current_paths)

    def initGui(self):
        self.popupMenu = QMenu(self.iface.mainWindow())
        self.open_connections_action = self._create_action("Add Vector Tiles Layer...", "server.svg", self._show_connections_dialog)
        self.reload_action = self._create_action(self._reload_button_text, "reload.svg", self._reload_tiles, False)
        self.export_action = self._create_action("Export loaded tiles", "save.svg", self._export_tiles)
        self.clear_cache_action = self._create_action("Clear cache", "delete.svg", FileHelper.clear_cache)
        self.iface.insertAddLayerAction(self.open_connections_action)  # Add action to the menu: Layer->Add Layer
        self.popupMenu.addAction(self.open_connections_action)
        self.popupMenu.addAction(self.reload_action)
        self.popupMenu.addAction(self.export_action)
        self.toolButton = QToolButton()
        self.toolButton.setMenu(self.popupMenu)
        self.toolButton.setDefaultAction(self.open_connections_action)
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButtonAction = self.iface.layerToolBar().addWidget(self.toolButton)
        self.about_action = self._create_action("About", "info.svg", self.show_about)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.about_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.open_connections_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.reload_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.export_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.clear_cache_action)
        info("Vector Tile Reader Plugin loaded...")

    def _update_nr_of_tiles(self):
        zoom = self._get_current_zoom()
        bounds = self._get_visible_extent_as_tile_bounds(scheme="xyz", zoom=zoom)
        nr_of_tiles = bounds["width"] * bounds["height"]
        self.connections_dialog.set_nr_of_tiles(nr_of_tiles)

    def _show_connections_dialog(self):
        self._update_nr_of_tiles()
        self.connections_dialog.show()

    def _export_tiles(self):
        from vt_writer import VtWriter
        # file_name = QFileDialog.getSaveFileName(None, "Export Vector Tiles", FileHelper.get_home_directory(), "mbtiles (*.mbtiles)")
        file_name = "C:\\Users\\Martin\\Downloads\\mbtiles\\test.mbtiles"
        if file_name:
            writer = VtWriter(self.iface, file_name)
            writer.export()

    def _reload_tiles(self):
        if self._current_source_path:
            self._create_progress_dialog(self.iface.mainWindow())
            scheme = self.reader.source.scheme()
            zoom = self._get_current_zoom()
            bounds = self._get_visible_extent_as_tile_bounds(scheme=scheme, zoom=zoom)
            self._load_tiles(path=self._current_source_path,
                             options=self.connections_dialog.options,
                             layers_to_load=self._current_layer_filter,
                             bounds=bounds,
                             ignore_limit=True)

    def _get_visible_extent_as_tile_bounds(self, scheme, zoom):
        e = self.iface.mapCanvas().extent().asWktCoordinates().split(", ")
        new_extent = map(lambda x: map(float, x.split(" ")), e)
        min_extent = new_extent[0]
        max_extent = new_extent[1]

        min_proj = epsg3857_to_wgs84_lonlat(min_extent[0], min_extent[1])
        max_proj = epsg3857_to_wgs84_lonlat(max_extent[0], max_extent[1])

        bounds = []
        bounds.extend(min_proj)
        bounds.extend(max_proj)
        tile_bounds = get_tile_bounds(zoom, bounds=bounds, scheme=scheme, crs="EPSG:4326")

        debug("Current extent: {}", tile_bounds)
        return tile_bounds

    def _on_connect(self, connection_name, path_or_url):
        debug("Connect to path_or_url: {}", path_or_url)

        self.reload_action.setText("{} ({})".format(self._reload_button_text, connection_name))

        try:
            reader = self._create_reader(path_or_url)
            self.reader = reader
            if reader:
                layers = reader.source.vector_layers()
                self.connections_dialog.set_layers(layers)
                self.connections_dialog.options.set_zoom(reader.source.min_zoom(), reader.source.max_zoom())
                self.reload_action.setEnabled(True)
                self._current_source_path = path_or_url
            else:
                self.connections_dialog.set_layers([])
                self.reload_action.setEnabled(False)
                self.reload_action.setText(self._reload_button_text)
                self._current_source_path = None
        except:
            QMessageBox.critical(None, "Unexpected Error", "An unexpected error occured. {}".format(str(sys.exc_info()[1])))

    def show_about(self):
        AboutDialog().show()

    def _on_add_layer(self, path_or_url, selected_layers):
        debug("add layer: {}", path_or_url)

        crs_string = self.reader.source.crs()
        self._init_qgis_map(crs_string)

        scheme = self.reader.source.scheme()
        zoom = self._get_current_zoom()
        extent = self._get_visible_extent_as_tile_bounds(scheme=scheme, zoom=zoom)
        # if not self.tilejson.is_within_bounds(zoom=zoom, extent=extent):
        #     pass  # todo: something's wrong here. probably a CRS mismatch between _get_visible_extent and tilejson
            # print "not in bounds"
            # self._set_qgis_extent(self.tilejson)

        keep_dialog_open = self.connections_dialog.keep_dialog_open()
        if keep_dialog_open:
            dialog_owner = self.connections_dialog
        else:
            dialog_owner = self.iface.mainWindow()
            self.connections_dialog.close()
        self._create_progress_dialog(dialog_owner)
        self._load_tiles(path=path_or_url,
                         options=self.connections_dialog.options,
                         layers_to_load=selected_layers,
                         bounds=extent)
        self._current_source_path = path_or_url
        self._current_layer_filter = selected_layers

    def _get_current_zoom(self):
        zoom = 14
        if self.reader:
            zoom = self.reader.source.max_zoom()
        if zoom is None:
            zoom = 14
        manual_zoom = self.connections_dialog.options.manual_zoom()
        if manual_zoom is not None:
            zoom = manual_zoom
        return zoom

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
        # self.iface.mapCanvas().mapSettings().setDestinationCrs(crs)
        self.iface.mapCanvas().mapRenderer().setDestinationCrs(crs)

    def _create_progress_dialog(self, owner):
        self.progress_dialog = ProgressDialog(owner)
        self.progress_dialog.on_cancel.connect(self._cancel_load)

    def _cancel_load(self):
        if self._current_reader:
            self._current_reader.cancel()

    def _create_action(self, title, icon, callback, is_enabled=True):
        new_action = QAction(QIcon(':/plugins/vector_tiles_reader/{}'.format(icon)), title, self.iface.mainWindow())
        new_action.triggered.connect(callback)
        new_action.setEnabled(is_enabled)
        return new_action

    def _load_tiles(self, path, options, layers_to_load, bounds=None, reader=None, ignore_limit=False):
        merge_tiles = options.merge_tiles_enabled()
        apply_styles = options.apply_styles_enabled()
        tile_limit = options.tile_number_limit()
        load_mask_layer = options.load_mask_layer_enabled()
        if ignore_limit:
            tile_limit = None
        manual_zoom = options.manual_zoom()
        cartographic_ordering = options.cartographic_ordering()

        if apply_styles:
            self._set_background_color()

        debug("Load: {}", path)
        if not reader:
            reader = self._create_reader(path)
            self._current_reader = reader
            self._current_options = options
        if reader:
            reader.enable_cartographic_ordering(enabled=cartographic_ordering)
            try:
                zoom = reader.source.max_zoom()
                if manual_zoom is not None:
                    zoom = manual_zoom
                reader.load_tiles(zoom_level=zoom,
                                  layer_filter=layers_to_load,
                                  load_mask_layer=load_mask_layer,
                                  merge_tiles=merge_tiles,
                                  apply_styles=apply_styles,
                                  max_tiles=tile_limit,
                                  bounds=bounds,
                                  limit_reacher_handler=lambda: self._show_limit_exceeded_message(tile_limit))
                self.refresh_layers()
                debug("Loading complete!")
            except RuntimeError:
                self._current_reader = None
                QMessageBox.critical(None, "Unexpected exception", str(sys.exc_info()[1]))
                critical(str(sys.exc_info()[1]))

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
        self.iface.layerToolBar().removeAction(self.toolButtonAction)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.about_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.open_connections_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.reload_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.export_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.clear_cache_action)
        self.iface.addLayerMenu().removeAction(self.open_connections_action)
