# -*- coding: utf-8 -*-
#
# This code is licensed under the GPL 2.0 license.
#
import unittest
import os
import sys
from qgis.core import *
from qgis.utils import iface
from PyQt4.QtCore import *
from vt_reader import VtReader
from util.connection import MBTILES_CONNECTION_TEMPLATE
import copy
import mock
from osgeo import gdal
from util.file_helper import clear_cache

class IfaceTests(unittest.TestCase):
    """
    Tests for Iface
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def testIfaceisNotNone(self):
        global iface
        self.assertIsNotNone(iface)

    @mock.patch("vt_reader.info")
    def test_load_from_vtreader(self, mock_info):
        global iface
        clear_cache()
        gdal.PushErrorHandler('CPLQuietErrorHandler')
        conn = copy.deepcopy(MBTILES_CONNECTION_TEMPLATE)
        conn["name"] = "Unittest_Connection"
        conn["path"] = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'uster_zh.mbtiles')
        reader = VtReader(iface=iface, connection=conn)
        bounds = {'y_min': 10644, 'y_max': 10645, 'zoom': 14, 'height': 2, 'width': 3, 'x_max': 8589, 'x_min': 8587}
        reader.set_options(max_tiles=5)
        reader._loading_options["zoom_level"] = 14
        reader._loading_options["bounds"] = bounds
        reader._load_tiles()
        mock_info.assert_any_call("Native decoding supported!!!")
        mock_info.assert_any_call("Import complete")


def suite():
    suite = unittest.makeSuite(IfaceTests, 'test')
    return suite


# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())


if __name__ == "__main__":
    run_all()
