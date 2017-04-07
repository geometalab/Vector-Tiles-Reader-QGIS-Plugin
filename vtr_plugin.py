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
from PyQt4.QtGui import QColor, QAction, QIcon, QMenu, QToolButton, QFileDialog, QMessageBox
from qgis.core import *

from file_helper import FileHelper
from log_helper import debug, info, warn, critical
from ui.dialogs import FileConnectionDialog, AboutDialog

import os
import sys
import site


class VtrPlugin:
    _dialog = None
    _model = None
    add_layer_action = None

    def __init__(self, iface):
        self.iface = iface
        self.settings = QSettings("Vector Tile Reader", "vectortilereader")
        self.recently_used = []
        self.file_dialog = FileConnectionDialog(FileHelper.get_home_directory())
        self.file_dialog.on_open.connect(self._on_open_mbtiles)

    def initGui(self):
        self._load_recently_used()
        self.add_layer_action = self._create_action("Add Vector Tiles Layer", "icon.png", self.run)
        self.about_action = self._create_action("About", "", self.show_about)
        self.iface.addPluginToMenu("&Vector Tiles Reader", self.about_action)
        self.iface.addPluginToMenu("&Vector Tiles Reader", self.add_layer_action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.add_layer_action)
        self.add_menu()
        info("Vector Tile Reader Plugin loaded...")

    def show_about(self):
        AboutDialog().show()

    def add_menu(self):
        self.popupMenu = QMenu(self.iface.mainWindow())
        default_action = self._create_action("Add Vector Tile Layer...", "icon.png", self.file_dialog.show)
        self.popupMenu.addAction(self._create_action("Add Vector Tile Layer...", "folder.svg", self.file_dialog.show))
        # self.popupMenu.addAction(self._create_action("Load url", "folder.svg", self._load_from_url))
        # self.recent = self.popupMenu.addMenu("Open Recent")
        # debug("Recently used: {}", self.recently_used)
        # for path in self.recently_used:
        #     debug("Create action: {}", path)
        #     self._add_recently_used(path)

        self.toolButton = QToolButton()
        self.toolButton.setMenu(self.popupMenu)
        self.toolButton.setDefaultAction(default_action)
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButtonAction = self.iface.addVectorToolBarWidget(self.toolButton)

    def _on_open_mbtiles(self, path):
        merge_tiles = self.file_dialog.is_merge_tiles_enabled()
        apply_styles = self.file_dialog.is_apply_styles_enabled()
        load_directory = self.file_dialog.load_directory_checked()
        debug("Load mbtiles: apply styles: {}, merge tiles: {}, load directory: {}, path: {}",
              apply_styles, merge_tiles, load_directory, path)
        self._load_from_disk(path, load_directory=load_directory, apply_styles=apply_styles, merge_tiles=merge_tiles)

    def _load_from_url(self):
        # todo: remove hardcoded url
        url = "http://192.168.0.18:6767/planet_osm_polygon/14/8568/5747.pbf"
        reader = self._create_reader(url)
        reader.load_vector_tiles(14)

    def _add_recently_used(self, path):
        if path not in self.recently_used:
            self.recently_used.append(path)
        self.recent.addAction(path, lambda path=path: self._load_mbtiles(path))

    def _load_from_disk(self, path, load_directory, apply_styles, merge_tiles):
        files_to_load = []
        if not load_directory and path and os.path.isfile(path):
            debug("Load file: {}", path)
            files_to_load.append(path)
            # self._add_recently_used(path)
            # self._save_recently_used()
        if load_directory and path and os.path.isdir(path):
            debug("Load directory: {}", path)
            for o in os.listdir(path):
                ext = os.path.splitext(o)[1]
                debug("dir entry: {}, ext: {}", o, ext)
                if ext == ".mbtiles":
                    file_path = os.path.join(path, o)
                    debug("This is a mbtiles file")
                    files_to_load.append(file_path)

        for f in files_to_load:
            self._load_mbtiles(f, apply_styles=apply_styles, merge_tiles=merge_tiles)

    def _create_action(self, title, icon, callback):
        new_action = QAction(QIcon(':/plugins/vectortilereader/{}'.format(icon)), title, self.iface.mainWindow())
        new_action.triggered.connect(callback)
        return new_action

    def _load_mbtiles(self, path, apply_styles, merge_tiles):
        reader = self._create_reader(path)
        if reader:
            is_valid = reader.is_mapbox_vector_tile()
            if is_valid:
                max_zoom = reader.get_max_zoom()
                if max_zoom:
                    reader.load_vector_tiles(zoom_level=max_zoom, load_mask_layer=False, merge_tiles=merge_tiles, apply_styles=apply_styles)
                else:
                    warn("Max Zoom not found, cannot load data")
            else:
                warn("File is not in Mapbox Vector Tile Format and cannot be loaded.")


    def _create_reader(self, mbtiles_path):
        self._add_path_to_dependencies_to_syspath()
        # A lazy import is required because the vtreader depends on the external libs
        from vt_reader import VtReader
        reader = None
        try:
            reader = VtReader(self.iface, mbtiles_path=mbtiles_path)
        except RuntimeError:
            QMessageBox.critical(None, "Loading failed", str(sys.exc_info()[1]))
        return reader

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
