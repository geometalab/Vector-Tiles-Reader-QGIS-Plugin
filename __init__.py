# -*- coding: utf-8 -*-

""" THIS COMMENT MUST NOT REMAIN INTACT

GNU GENERAL PUBLIC LICENSE

Copyright (c) 2017 geometalab HSR

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

"""


def name():
    return "vector_tiles_reader"


def description():
    return "This Python plugin reads Mapbox Vector Tiles (MVT) from vector tile servers, local MBTiles files or from a t-rex cache."


def version():
    return "Version 1.2.1"


def qgisMinimumVersion():
    return "2.18"


def qgisMaximumVersion():
    return "2.99"


def classFactory(iface):
    from vtr_plugin import VtrPlugin
    return VtrPlugin(iface)
