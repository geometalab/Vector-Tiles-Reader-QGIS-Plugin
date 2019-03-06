# -*- coding: utf-8 -*-
#
# This code is licensed under the GPL 2.0 license.
#
from qgis.testing import unittest
import os
import sys
from util.tile_source import MBTilesSource


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
        path = _get_path("uster_zh.mbtiles", directory=_sample_dir())
        src = _create(path)
        self.assertIsNotNone(src)
        self.assertEqual(path, src.source())

    def test_non_existing_file(self):
        path = _get_path("doesnotexist.txt")
        with self.assertRaises(RuntimeError) as ctx:
            MBTilesSource(path)
        error = "The file does not exist: {}".format(path)
        self.assertTrue(error in ctx.exception)

    def test_non_mbtiles(self):
        path = _get_path("textfile.txt")
        with self.assertRaises(RuntimeError) as ctx:
            MBTilesSource(path)
        error = "The file '{}' is not a valid Mapbox vector tile file and cannot be loaded.".format(path)
        self.assertTrue(error in ctx.exception)

    def test_get_bounds(self):
        src = _create("uster_zh.mbtiles", directory=_sample_dir())
        b = src.bounds()
        self.assertEqual((8.67765, 47.3201, 8.76074, 47.38406), b)

    def test_scheme_metadata(self):
        src = _create("uster_zh.mbtiles", directory=_sample_dir())
        scheme = src._get_metadata_value("scheme")
        self.assertIsNone(scheme)

    def test_scheme_default(self):
        src = _create("uster_zh.mbtiles", directory=_sample_dir())
        self.assertEqual("tms", src.scheme())

    def test_get_bounds_tile(self):
        src = _create("uster_zh.mbtiles", directory=_sample_dir())
        b = src.bounds_tile(zoom=14)
        bounds_expected = {
            "y_min": 10642,
            "y_max": 10647,
            "zoom": 14,
            "height": 6,
            "width": 5,
            "x_max": 8590,
            "x_min": 8586,
            "scheme": "tms",
        }
        self.assertEqual(bounds_expected, b)

    def test_get_bounds_from_data(self):
        src = _create("uster_zh.mbtiles", directory=_sample_dir())
        b = src.bounds_tile(zoom=14)
        data_bounds = src._get_bounds_from_data(zoom_level=14)
        self.assertEqual(data_bounds, b)

    def test_load_tiles(self):
        src = _create("uster_zh.mbtiles", directory=_sample_dir())
        with self.assertRaises(RuntimeError) as ctx:
            src.load_tiles(14, None)
        error = "tiles_to_load is required"
        self.assertTrue(error in ctx.exception)

    def test_load_tiles_without_zoom(self):
        src = _create("uster_zh.mbtiles", directory=_sample_dir())
        with self.assertRaises(RuntimeError) as ctx:
            src.load_tiles(None, None)
        error = "zoom_level is required"
        self.assertTrue(error in ctx.exception)

    def test_load_tiles_restricted(self):
        src = _create("uster_zh.mbtiles", directory=_sample_dir())
        all_tile_data_tuples = src.load_tiles(14, tiles_to_load=[(8586, 10642)])
        self.assertEqual(1, len(all_tile_data_tuples))
        self.assertEqual((8586, 10642), all_tile_data_tuples[0][0].coord())

    def test_load_tiles_with_limit_zero(self):
        src = _create("uster_zh.mbtiles", directory=_sample_dir())
        all_tiles = src.load_tiles(14, tiles_to_load=[], max_tiles=0)
        self.assertEqual(0, len(all_tiles))

    def test_load_tiles_with_limit_and_no_tiles_to_load(self):
        src = _create("uster_zh.mbtiles", directory=_sample_dir())
        all_tiles = src.load_tiles(14, tiles_to_load=[], max_tiles=10)
        self.assertEqual(0, len(all_tiles))

    def test_load_tiles_with_tiles_to_load(self):
        src = _create("uster_zh.mbtiles", directory=_sample_dir())
        all_tiles = src.load_tiles(14, tiles_to_load=[(8586, 10642)], max_tiles=2)
        self.assertEqual(1, len(all_tiles))
        self.assertEqual((8586, 10642), all_tiles[0][0].coord())

    def test_where_clause(self):
        src = _create("uster_zh.mbtiles", directory=_sample_dir())
        where_clause = src._get_where_clause(tiles_to_load=[], zoom_level=14)
        self.assertEqual('WHERE zoom_level = 14 AND tile_column || ";" || tile_row IN ()', where_clause)


def _sample_dir():
    return os.path.join(os.path.dirname(__file__), "..", "sample_data")


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
    s = unittest.makeSuite(MbtileSourceTests, "test")
    return s


# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())


if __name__ == "__main__":
    run_all()
