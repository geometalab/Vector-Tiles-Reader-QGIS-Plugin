# -*- coding: utf-8 -*-
#
# This code is licensed under the GPL 2.0 license.
#
import unittest
import os
import sys
from ..util.tile_source import MBTilesSource


class MbtileSourceTests(unittest.TestCase):
    """
    Tests for MBTilesSource
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_mbtiles_source_creation(self):
        src = _create('uster_zh.mbtiles', directory=_sample_dir())
        self.assertIsNotNone(src)

    def test_non_mbtiles(self):
        path = _get_path("textfile.txt")
        with self.assertRaises(RuntimeError) as ctx:
            MBTilesSource(path)
        error = "The file '{}' is not a valid Mapbox vector tile file and cannot be loaded.".format(path)
        self.assertTrue(error in ctx.exception)


def _sample_dir():
    return os.path.join(os.path.dirname(__file__), "..", 'sample_data')


def _get_path(mbtiles_file, directory=None):
    if directory:
        path = os.path.join(directory, mbtiles_file)
    else:
        path = os.path.join(os.path.dirname(__file__), "data", mbtiles_file)
    return path


def _create(mbtiles_file, directory=None):
    path = _get_path(mbtiles_file=mbtiles_file, directory=directory)
    return MBTilesSource(path)


def suite():
    s = unittest.makeSuite(MbtileSourceTests, 'test')
    return s


# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())


if __name__ == "__main__":
    run_all()
