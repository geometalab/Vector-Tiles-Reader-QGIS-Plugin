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
    return "vtr"


def description():
    return "Reads Mapbox Vector Tiles"


def version():
    return "Version 0.0.9"


def qgisMinimumVersion():
    return "2.18"


def qgisMaximumVersion():
    return "2.18"


def classFactory(iface):
    from vtr_plugin import VtrPlugin
    return VtrPlugin(iface)
