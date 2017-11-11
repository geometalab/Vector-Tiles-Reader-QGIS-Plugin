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
from ..util.tile_source import MBTilesSource


class MbtileSourceTests(unittest.TestCase):
    """
    Tests for Iface
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_mbtiles_source_creation(self):
        path = os.path.join(os.path.dirname(__file__), "..", 'sample_data', 'uster_zh.mbtiles')
        src = MBTilesSource(path)
        self.assertIsNotNone(src)
        self.assertEqual(path, src.source())


def suite():
    s = unittest.makeSuite(MbtileSourceTests, 'test')
    return s


# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())


if __name__ == "__main__":
    run_all()
