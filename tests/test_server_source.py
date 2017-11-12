# -*- coding: utf-8 -*-
#
# This code is licensed under the GPL 2.0 license.
#
import unittest
import os
import sys
from util.tile_source import ServerSource
import mock


class ServerSourceTests(unittest.TestCase):
    """
    Tests for MBTilesSource
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_openmaptiles(self):
        url = "https://free.tilehosting.com/data/v3.json?key=6irhAXGgsi8TrIDL0211"
        src = ServerSource(url)
        self.assertIsNotNone(src)
        self.assertEqual(url, src.source())

    def test_mapzen(self):
        url = "http://tile.mapzen.com/mapzen/vector/v1/tilejson/mapbox.json?api_key=mapzen-7SNUCXx"
        src = ServerSource(url)
        self.assertIsNotNone(src)
        self.assertEqual(url, src.source())

    def test_non_existing_url(self):
        with self.assertRaises(RuntimeError) as ctx:
            ServerSource("http://localhost/mytilejson.json")
        error = "HTTP HEAD failed: status None"
        self.assertTrue(error in ctx.exception)

    @mock.patch("util.tile_source.url_exists", return_value=(True, None))
    def test_load(self, mock_url_exists):
        src = ServerSource("https://localhost")
        mock_url_exists.assert_called_with("https://localhost")

    # def test_get_bounds(self):
    #     src = _create('uster_zh.mbtiles', directory=_sample_dir())
    #     b = src.bounds()
    #     self.assertEqual([8.67765, 47.3201, 8.76074, 47.38406], b)
    #
    # def test_scheme_metadata(self):
    #     src = _create('uster_zh.mbtiles', directory=_sample_dir())
    #     scheme = src._get_metadata_value("scheme")
    #     self.assertIsNone(scheme)
    #
    # def test_scheme_default(self):
    #     src = _create('uster_zh.mbtiles', directory=_sample_dir())
    #     self.assertEqual("tms", src.scheme())
    #
    # def test_get_bounds_tile(self):
    #     src = _create('uster_zh.mbtiles', directory=_sample_dir())
    #     b = src.bounds_tile(zoom=14)
    #     bounds_expected = {
    #         'y_min': 10642,
    #         'y_max': 10647,
    #         'zoom': 14,
    #         'height': 6,
    #         'width': 5,
    #         'x_max': 8590,
    #         'x_min': 8586}
    #     self.assertEqual(bounds_expected, b)
    #
    # def test_get_bounds_from_data(self):
    #     src = _create('uster_zh.mbtiles', directory=_sample_dir())
    #     b = src.bounds_tile(zoom=14)
    #     data_bounds = src._get_bounds_from_data(zoom_level=14)
    #     self.assertEqual(data_bounds, b)
    #
    # def test_load_tiles(self):
    #     src = _create('uster_zh.mbtiles', directory=_sample_dir())
    #     with self.assertRaises(RuntimeError) as ctx:
    #         src.load_tiles(14, None)
    #     error = "tiles_to_load is required"
    #     self.assertTrue(error in ctx.exception)
    #
    # def test_load_tiles_without_zoom(self):
    #     src = _create('uster_zh.mbtiles', directory=_sample_dir())
    #     with self.assertRaises(RuntimeError) as ctx:
    #         src.load_tiles(None, None)
    #     error = "zoom_level is required"
    #     self.assertTrue(error in ctx.exception)
    #
    # def test_load_tiles_restricted(self):
    #     src = _create('uster_zh.mbtiles', directory=_sample_dir())
    #     all_tile_data_tuples = src.load_tiles(14, tiles_to_load=[(8586, 10642)])
    #     self.assertEqual(1, len(all_tile_data_tuples))
    #     self.assertEqual((8586, 10642), all_tile_data_tuples[0][0].coord())
    #
    # def test_load_tiles_with_limit_zero(self):
    #     src = _create('uster_zh.mbtiles', directory=_sample_dir())
    #     all_tiles = src.load_tiles(14, tiles_to_load=[], max_tiles=0)
    #     self.assertEqual(0, len(all_tiles))
    #
    # def test_load_tiles_with_limit_and_no_tiles_to_load(self):
    #     src = _create('uster_zh.mbtiles', directory=_sample_dir())
    #     all_tiles = src.load_tiles(14, tiles_to_load=[], max_tiles=10)
    #     self.assertEqual(0, len(all_tiles))
    #
    # def test_load_tiles_with_tiles_to_load(self):
    #     src = _create('uster_zh.mbtiles', directory=_sample_dir())
    #     all_tiles = src.load_tiles(14, tiles_to_load=[(8586, 10642)], max_tiles=2)
    #     self.assertEqual(1, len(all_tiles))
    #     self.assertEqual((8586, 10642), all_tiles[0][0].coord())
    #
    # def test_where_clause(self):
    #     src = _create('uster_zh.mbtiles', directory=_sample_dir())
    #     where_clause = src._get_where_clause(tiles_to_load=[], zoom_level=14)
    #     self.assertEqual('WHERE zoom_level = 14 AND tile_column || ";" || tile_row IN ()', where_clause)


def suite():
    s = unittest.makeSuite(ServerSourceTests, 'test')
    return s


# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())


if __name__ == "__main__":
    run_all()
