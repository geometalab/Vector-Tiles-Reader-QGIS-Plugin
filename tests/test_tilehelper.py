import unittest
from util.tile_helper import *


class TileHelperTests(unittest.TestCase):
    """
    Tests for Iface
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_change_scheme(self):
        self.assertEqual(0, change_scheme(zoom=0, y=0))
        self.assertEqual(0, change_scheme(zoom=1, y=1))
        self.assertEqual(166, change_scheme(zoom=8, y=89))
        self.assertEqual(2729017, change_scheme(zoom=22, y=1465286))

    def test_latlon_to_tile_tms(self):
        tms_tile = latlon_to_tile(0, WORLD_BOUNDS[1], WORLD_BOUNDS[0], source_crs=4326, scheme="tms")
        self.assertEquals((0, 0), tms_tile)

    def test_latlon_to_tile_xyz(self):
        xyz_tile = latlon_to_tile(0, WORLD_BOUNDS[1], WORLD_BOUNDS[0], source_crs=4326, scheme="xyz")
        self.assertEquals(xyz_tile, (0, 0))

    def test_get_zoom_by_scale_min(self):
        zoom = get_zoom_by_scale(-1)
        self.assertEqual(23, zoom)

    def test_get_zoom_by_scale_max(self):
        zoom = get_zoom_by_scale(10000000000)
        self.assertEqual(0, zoom)

    def test_get_epsg(self):
        self.assertEqual(3857, get_code_from_epsg("epsg:3857"))
