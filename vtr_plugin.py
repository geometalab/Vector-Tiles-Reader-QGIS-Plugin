# -*- coding: utf-8 -*-

""" THIS COMMENT MUST NOT REMAIN INTACT

GNU GENERAL PUBLIC LICENSE

Copyright (c) 2017 geometalab HSR

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

"""

from PyQt4.QtCore import QSettings
from PyQt4.QtGui import QAction, QIcon, QMenu, QToolButton,  QMessageBox
from qgis.core import *

from file_helper import FileHelper
from log_helper import debug, info, warn, critical
from tile_helper import get_tile_bounds
from tile_json import TileJSON
from ui.dialogs import FileConnectionDialog, AboutDialog, ProgressDialog, ServerConnectionDialog

import os
import sys
import site


class VtrPlugin:
    _dialog = None
    _model = None
    add_layer_action = None

    def __init__(self, iface):
        self._add_path_to_dependencies_to_syspath()
        self.iface = iface
        self.iface.mapCanvas().extentsChanged.connect(self._on_map_extent_changed)
        self.settings = QSettings("Vector Tile Reader", "vectortilereader")
        self.recently_used = []
        self.file_dialog = FileConnectionDialog(FileHelper.get_home_directory())
        self.file_dialog.on_open.connect(self._on_open_mbtiles)
        self.file_dialog.on_valid_file_path_changed.connect(self._update_zoom_from_file)
        self.server_dialog = ServerConnectionDialog()
        self.server_dialog.on_connect.connect(self._on_connect)
        self.server_dialog.on_add.connect(self._on_add_server_layer)

    def initGui(self):
        self._load_recently_used()
        self.add_layer_action = self._create_action("Add Vector Tiles Layer...", "icon.png", self.run)
        self.about_action = self._create_action("About", "", self.show_about)
        self.iface.addPluginToMenu("&Vector Tiles Reader", self.about_action)
        self.iface.addPluginToMenu("&Vector Tiles Reader", self.add_layer_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.add_layer_action)
        self.iface.addLayerMenu().addAction(self.add_layer_action)  # Add action to the menu: Layer->Add Layer
        self.add_menu()
        self.progress_dialog = ProgressDialog()
        info("Vector Tile Reader Plugin loaded...")

    def _on_map_extent_changed(self):
        b = self._get_visible_extent_as_tile_bounds()
        print(b)

    def _get_visible_extent_as_tile_bounds(self):
        import pyproj
        e = self.iface.mapCanvas().extent().asWktCoordinates().split(", ")
        e = map(lambda x: map(float, x.split(" ")), e)
        min_extent = e[0]
        max_extent = e[1]
        wgs84 = pyproj.Proj("+init=EPSG:4326")
        espg3857 = pyproj.Proj("+init=EPSG:3857")
        min_proj = pyproj.transform(espg3857, wgs84, min_extent[0], min_extent[1])
        max_proj = pyproj.transform(espg3857, wgs84, max_extent[0], max_extent[1])

        bounds = []
        bounds.extend(min_proj)
        bounds.extend(max_proj)

        tile = get_tile_bounds(14, bounds=bounds)
        return tile

    def _on_connect(self, url):
        debug("Connect to url: {}", url)
        tilejson = TileJSON(url)
        if tilejson.load():
            layers = tilejson.vector_layers()
            self.server_dialog.set_layers(layers)
        else:
            self.server_dialog.set_layers([])
            tilejson = None
        self.tilejson = tilejson

    def _on_add_server_layer(self):
        assert self.tilejson
        url = self.tilejson.tiles()[0]
        apply_styles = self.server_dialog.apply_styles_enabled()
        merge_tiles = self.server_dialog.merge_tiles_enabled()
        debug("Add layer: {}", url)

        tiles = self._get_tiles_to_load(14)
        for t in tiles:
            zoom = str(t[0])
            col = str(t[1])
            row = str(t[2])
            newurl = url.replace("{z}", zoom).replace("{x}", col).replace("{y}", row)
            debug("Loading url: {}", newurl)
            reader = self._create_reader(newurl)
            if reader:
                reader.load_tiles(14, apply_styles=apply_styles, merge_tiles=merge_tiles)

            # todo: remove after debugging
            break

    def _get_tiles_to_load(self, zoom):
        extent = self._get_visible_extent_as_tile_bounds()
        nr_tiles_x = extent[1][0] - extent[0][0] + 1
        nr_tiles_y = extent[1][1] - extent[0][1] + 1
        tiles = []
        for x in range(nr_tiles_x):
            for y in range(nr_tiles_y):
                col = x + extent[0][0]
                row = y + extent[0][1]
                tiles.append((zoom, col, row))
        debug("tiles to load: {}", tiles)
        return tiles


    def _update_zoom_from_file(self, path):
        min_zoom = None
        max_zoom = None
        reader = self._create_reader(path)
        if reader:
            min_zoom = reader.get_min_zoom()
            max_zoom = reader.get_max_zoom()
        else:
            self.file_dialog.clear_path()
        self.file_dialog.set_zoom(min_zoom, max_zoom)

    def show_about(self):
        AboutDialog().show()

    def add_menu(self):
        self.popupMenu = QMenu(self.iface.mainWindow())
        open_file_action = self._create_action("Add Vector Tile Layer...", "icon.png", self.file_dialog.show)
        open_server_action = self._create_action("Add Vector Tile Server Layer...", "folder.svg", self.server_dialog.show)
        self.popupMenu.addAction(self._create_action("Add Vector Tile Layer...", "folder.svg", self.file_dialog.show))
        self.popupMenu.addAction(open_server_action)
        # self.popupMenu.addAction(self._create_action("Load url", "folder.svg", self._load_from_url))
        # self.recent = self.popupMenu.addMenu("Open Recent")
        # debug("Recently used: {}", self.recently_used)
        # for path in self.recently_used:
        #     debug("Create action: {}", path)
        #     self._add_recently_used(path)

        self.toolButton = QToolButton()
        self.toolButton.setMenu(self.popupMenu)
        # self.toolButton.setDefaultAction(open_file_action)
        self.toolButton.setDefaultAction(open_server_action)
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButtonAction = self.iface.addVectorToolBarWidget(self.toolButton)

    def _on_open_mbtiles(self, path):
        merge_tiles = self.file_dialog.is_merge_tiles_enabled()
        apply_styles = self.file_dialog.is_apply_styles_enabled()
        tile_number_limit = self.file_dialog.get_tile_number_limit()
        manual_zoom = self.file_dialog.get_manual_zoom()
        debug("Load mbtiles: apply styles: {}, merge tiles: {}, tilelimit: {}, manual_zoom: {}, path: {}",
              apply_styles, merge_tiles, tile_number_limit, manual_zoom, path)
        self._load_from_disk(path=path,
                             apply_styles=apply_styles,
                             merge_tiles=merge_tiles,
                             tile_number_limit=tile_number_limit,
                             manual_zoom=manual_zoom)

    def _load_from_url(self):
        # todo: remove hardcoded url
        url = "http://192.168.0.18:6767/planet_osm_polygon/14/8568/5747.pbf"
        reader = self._create_reader(url)
        reader.load_tiles(14)

    # def _add_recently_used(self, path):
    #     if path not in self.recently_used:
    #         self.recently_used.append(path)
    #     self.recent.addAction(path, lambda path=path: self._load_mbtiles(path))

    def _load_from_disk(self, path, apply_styles, merge_tiles, tile_number_limit, manual_zoom):
        if path and os.path.isfile(path):
            debug("Load file: {}", path)
            # self._add_recently_used(path)
            # self._save_recently_used()
            self._load_mbtiles(path,
                               apply_styles=apply_styles,
                               merge_tiles=merge_tiles,
                               tile_limit=tile_number_limit,
                               manual_zoom=manual_zoom)

    def _create_action(self, title, icon, callback):
        new_action = QAction(QIcon(':/plugins/vectortilereader/{}'.format(icon)), title, self.iface.mainWindow())
        new_action.triggered.connect(callback)
        return new_action

    def _load_mbtiles(self, path, apply_styles, merge_tiles, tile_limit, manual_zoom):
        reader = self._create_reader(path)
        if reader:
            try:
                is_valid = reader.is_mapbox_vector_tile()
                if is_valid:
                    max_zoom = reader.get_max_zoom()
                    min_zoom = reader.get_min_zoom()
                    debug("valid zoom range: {} - {}", min_zoom, max_zoom)
                    debug("manual zoom: {}", manual_zoom)
                    zoom = max_zoom
                    if manual_zoom is not None:
                        zoom = VtrPlugin.clamp(min_zoom, manual_zoom, max_zoom)
                    if zoom is not None:
                        debug("Zoom: {}", zoom)
                        reader.load_tiles(
                            zoom_level=zoom,
                            load_mask_layer=False,
                            merge_tiles=merge_tiles,
                            apply_styles=apply_styles,
                            tilenumber_limit=tile_limit)
                    else:
                        warn("Max Zoom not found, cannot load data")
                else:
                    warn("File is not in Mapbox Vector Tile Format and cannot be loaded.")
            except RuntimeError:
                QMessageBox.critical(None, "Unexpected exception", str(sys.exc_info()[1]))
                critical(str(sys.exc_info()[1]))

    @staticmethod
    def clamp(minimum, x, maximum):
        return max(minimum, min(x, maximum))

    def _create_reader(self, mbtiles_path):
        # A lazy import is required because the vtreader depends on the external libs
        from vt_reader import VtReader
        reader = None
        try:
            reader = VtReader(self.iface, mbtiles_path=mbtiles_path, progress_handler=self.handle_progress_update)
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
        self.iface.removeVectorToolBarIcon(self.toolButtonAction)
        self.iface.removePluginMenu("&Vector Tiles Reader", self.add_layer_action)
        self.iface.removePluginMenu("&Vector Tiles Reader", self.about_action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.add_layer_action)
        self.iface.addLayerMenu().removeAction(self.add_layer_action)

    def run(self):
        self.file_dialog.show()

    def _load_recently_used(self):
        recently_used = FileHelper.get_recently_used_file()
        if os.path.isfile(recently_used):
            with open(recently_used, 'r') as f:
                for line in f:
                    line = line.rstrip("\n")
                    if os.path.isfile(line):
                        debug("recently used: {}", line)
                        self.recently_used.append(line)

    def _save_recently_used(self):
        recently_used = FileHelper.get_recently_used_file()
        with open(recently_used, 'w') as f:
            for path in self.recently_used:
                f.write("{}\n".format(path))
