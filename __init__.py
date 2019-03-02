# -*- coding: utf-8 -*-

""" THIS COMMENT MUST NOT REMAIN INTACT

GNU GENERAL PUBLIC LICENSE

Copyright (c) 2017 geometalab HSR

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

"""
import os
import sys
import site

ext_libs_path = os.path.join(os.path.dirname(__file__), 'ext-libs')
if ext_libs_path not in sys.path:
    site.addsitedir(ext_libs_path)


def classFactory(iface):
    from .vtr_plugin import VtrPlugin
    return VtrPlugin(iface)


def run_all():
    import sys
    import os
    os.environ["VTR_TESTS"] = '1'
    sys.path.append(".")
    sys.path.append("../vector-tiles-reader/util")
    sys.path.append("../vector-tiles-reader")
    sys.path.append("../vector-tiles-reader/ext-libs")
    from .tests import test_all
    test_all.run_all()