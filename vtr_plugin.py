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
from vt_reader import VtReader
import resources


class VtrPlugin:
    _dialog = None
    _model = None
    action = None

    def __init__(self, iface):
        # save reference to the QGIS interface
        self.iface = iface
        self.settings = QSettings("Vector Tile Reader","vectortilereader")
        print "now importing all required stuff"
        import sys
        import os
        import site
        site.addsitedir(os.path.abspath(os.path.dirname(__file__) + '/ext-libs'))
        print "import google.protobuf"
        import google.protobuf
        print "importing google.protobuf succeeded"
        print "import mapbox_vector_tile"
        import mapbox_vector_tile 
        print "importing mapbox_vector_tile succeeded"

    def initGui(self):
        print "VTR Plugin initGui"
        self.action = QAction(QIcon(':/plugins/vectortilereader/icon.png'), "Add Vector Tiles Layer", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addVectorToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Vector Tiles Reader", self.action)
        self.iface.addPluginToVectorMenu("&Vector Tiles Reader", self.action)

        self.reader = VtReader(self.iface)
        self.reader.do_work()

    def unload(self):
        print "VTR Plugin unload"
        # Remove the plugin menu item and icon
        self.iface.removeVectorToolBarIcon(self.action)
        self.iface.removePluginMenu("&Vector Tiles Reader", self.action)
        self.iface.removePluginVectorMenu("&Vector Tiles Reader", self.action)

    def run(self):
        # create and show a configuration dialog or something similar
        print "VTR Plugin: run called!"
        self.reader.do_work()