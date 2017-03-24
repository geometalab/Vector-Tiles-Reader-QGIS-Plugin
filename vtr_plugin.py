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
from PyQt4.QtGui import QAction, QIcon, QMenu, QToolButton, QFileDialog, QMessageBox
from qgis.core import *

from file_helper import FileHelper
from log_helper import debug, info, warn, critical

import os
import sys
import site
from sourcedialog import SourceDialog


class VtrPlugin:
    _dialog = None
    _model = None
    action = None

    def __init__(self, iface):
        self.iface = iface
        self.settings = QSettings("Vector Tile Reader", "vectortilereader")
        self._init_openfile_dialog()
        self.recently_used = []

    def _init_openfile_dialog(self):
        dlg = QFileDialog()
        dlg.setNameFilter("Mapbox Tiles (*.mbtiles)")
        dlg.setOption(QFileDialog.DontUseNativeDialog)
        self.open_mbtile_dialog = dlg


    def initGui(self):
        self._load_recently_used()
        self.action = QAction(QIcon(':/plugins/vectortilereader/icon.png'), "Add Vector Tiles Layer", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&Vector Tiles Reader", self.action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.action)
        self.settingsaction = QAction(QIcon(':/plugins/vectortilereader/icon.png'), "Settings", self.iface.mainWindow())
        self.settingsaction.triggered.connect(self.edit_sources)
        self.iface.addPluginToMenu("&Vector Tiles Reader", self.settingsaction)
        self.add_menu()
        info("Vector Tile Reader Plugin loaded...")

    def add_menu(self):
        self.popupMenu = QMenu(self.iface.mainWindow())
        default_action = self._create_action("Add Vector Tiles Layer", "icon.png", self.run)
        self.popupMenu.addAction(default_action)
        self.popupMenu.addAction(self._create_action("Open Mapbox Tiles...", "folder.svg", self._open_file_browser))

        self.recent = self.popupMenu.addMenu("Open Recent")
        debug("Recently used: {}", self.recently_used)
        for path in self.recently_used:
            debug("Create action: {}", path)
            self._add_recently_used(path)

        self.toolButton = QToolButton()
        self.toolButton.setMenu(self.popupMenu)
        self.toolButton.setDefaultAction(default_action)
        self.toolButton.setPopupMode(QToolButton.MenuButtonPopup)
        self.toolButtonAction = self.iface.addVectorToolBarWidget(self.toolButton)

    def _add_recently_used(self, path):
        if path not in self.recently_used:
            self.recently_used.append(path)
        self.recent.addAction(path, lambda path=path: self._load_mbtiles(path))

    def _open_file_browser(self):
        path = QFileDialog.getOpenFileName(self.iface.mainWindow(), "Select Mapbox Tiles", "", "Mapbox Tiles (*.mbtiles)")
        if path and os.path.isfile(path):
            self._add_recently_used(path)
            self._save_recently_used()
            self._load_mbtiles(path)

    def _create_action(self, title, icon, callback):
        new_action = QAction(QIcon(':/plugins/vectortilereader/{}'.format(icon)), title, self.iface.mainWindow())
        new_action.triggered.connect(callback)
        return new_action

    def _load_mbtiles(self, path):
        reader = self._create_reader(path)
        if reader:
            is_valid = reader.is_mapbox_vector_tile()
            if is_valid:
                max_zoom = reader.get_max_zoom()
                if max_zoom:
                    reader.load_vector_tiles(max_zoom)
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
        self.iface.removePluginMenu("&Vector Tiles Reader", self.action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.action)
        self.iface.removePluginMenu("&Vector Tiles Reader", self.settingsaction)

    def run(self):
        self._open_file_browser()

    def edit_sources(self):
        dlg = SourceDialog()
        dlg.setModal(True)
        dlg.connect(dlg.btnClose, SIGNAL("clicked()"), dlg.close)
        dlg.exec_()

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
