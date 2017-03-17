# -*- coding: utf-8 -*-

""" THIS COMMENT MUST NOT REMAIN INTACT

GNU GENERAL PUBLIC LICENSE

Copyright (c) 2017 geometalab HSR

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

"""

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from log_helper import info

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
        self.settings = QSettings("Vector Tile Reader","vectortilereader")

    def initGui(self):
        self.action = QAction(QIcon(':/plugins/vectortilereader/icon.png'), "Add Vector Tiles Layer", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addVectorToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Vector Tiles Reader", self.action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.action)

        self.settingsaction = QAction(QIcon(':/plugins/vectortilereader/icon.png'), "Settings", self.iface.mainWindow())
        self.settingsaction.triggered.connect(self.edit_sources)
        self.iface.addPluginToMenu("&Vector Tiles Reader", self.settingsaction)
        self.init_vt_reader()
        info("Vector Tile Reader Plugin loaded...")

    def init_vt_reader(self):
        self._add_path_to_dependencies_to_syspath()
        # A lazy import is required because the vtreader depends on the external libs
        from vt_reader import VtReader
        self.reader = VtReader(self.iface)

    def _add_path_to_dependencies_to_syspath(self):
        """
         * Adds the path to the external libraries to the sys.path if not already added
        """
        ext_libs_path = os.path.abspath(os.path.dirname(__file__) + '/ext-libs')
        if ext_libs_path not in sys.path:
            site.addsitedir(ext_libs_path)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removeVectorToolBarIcon(self.action)
        self.iface.removePluginMenu("&Vector Tiles Reader", self.action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.action)
        self.iface.removePluginMenu("&Vector Tiles Reader", self.settingsaction)

    def run(self):
        # create and show a configuration dialog or something similar
        self.reader.load_vector_tiles(zoom_level=14)

    def edit_sources(self):
        dlg = SourceDialog()
        dlg.setModal(True)
        dlg.connect(dlg.btnClose, SIGNAL("clicked()"), dlg.close)
        dlg.exec_()
