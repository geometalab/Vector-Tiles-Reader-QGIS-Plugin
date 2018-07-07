# -*- coding: utf-8 -*-
#
# This code is licensed under the GPL 2.0 license.
#
import unittest
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

    def test_non_existing_url(self):
        with self.assertRaises(RuntimeError) as ctx:
            ServerSource("http://localhost/mytilejson.json")
        error = "Loading error: Connection refused\n\nURL incorrect? (HTTP Status None)"
        print(ctx.exception)
        self.assertTrue(error in ctx.exception)

    @mock.patch("util.tile_source.TileJSON")
    @mock.patch("util.tile_source.load_tiles_async", return_value=[((1, 2), 'data')])
    @mock.patch("util.tile_source.url_exists", return_value=(True, None))
    def test_load(self, mock_url_exists, mock_load_tiles_async, mock_tile_json):
        src = ServerSource("https://localhost")
        mock_url_exists.assert_called_with("https://localhost")
        tiles = src.load_tiles(14, [(1, 1)])
        self.assertEqual(1, len(tiles))


def suite():
    s = unittest.makeSuite(ServerSourceTests, 'test')
    return s


# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())


if __name__ == "__main__":
    run_all()
