import sys
from qgis.testing import unittest
from util.tile_helper import (
    Bounds,
    center_tiles_equal,
    convert_coordinate,
    change_scheme,
    WORLD_BOUNDS,
    latlon_to_tile,
    get_zoom_by_scale,
    get_code_from_epsg,
    get_tile_bounds,
    get_tiles_from_center,
)
import itertools


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

    def test_convert_coordinate(self):
        target_lon = 951781.6462824893
        target_lat = 6053782.39151094
        lon, lat = convert_coordinate(4326, 3857, 47.68, 8.55)
        print(lon, lat)
        assert lon == target_lon
        assert lat == target_lat

    def test_change_scheme(self):
        self.assertEqual(0, change_scheme(zoom=0, y=0))
        self.assertEqual(0, change_scheme(zoom=1, y=1))
        self.assertEqual(166, change_scheme(zoom=8, y=89))
        self.assertEqual(2729017, change_scheme(zoom=22, y=1465286))

    def test_top_left_latlon_to_tile_for_each_zoom(self):
        for n in range(0, 24):
            top_left = latlon_to_tile(zoom=n, lat=WORLD_BOUNDS[3], lng=WORLD_BOUNDS[0], source_crs=4326, scheme="xyz")
            self.assertEqual((0, 0), top_left, "Zoom level {} incorrect".format(n))

    def test_bottom_right_latlon_to_tile_for_each_zoom(self):
        for n in range(0, 24):
            bottom_right = latlon_to_tile(
                zoom=n, lat=WORLD_BOUNDS[1], lng=WORLD_BOUNDS[2], source_crs=4326, scheme="xyz"
            )
            max_tile = (2 ** n) - 1
            self.assertEqual((max_tile, max_tile), bottom_right, "Zoom level {} incorrect".format(n))

    def test_latlon_to_tile_tms(self):
        tms_tile = latlon_to_tile(0, WORLD_BOUNDS[1], WORLD_BOUNDS[0], source_crs=4326, scheme="tms")
        self.assertEquals((0, 0), tms_tile)

    def test_latlon_to_tile_xyz(self):
        xyz_tile = latlon_to_tile(0, WORLD_BOUNDS[1], WORLD_BOUNDS[0], source_crs=4326, scheme="xyz")
        self.assertEquals(xyz_tile, (0, 0))

    def test_latlon_to_tile_manual(self):
        web_mercator_pos = (981106, 5978646)
        tms = latlon_to_tile(zoom=6, lat=web_mercator_pos[1], lng=web_mercator_pos[0], source_crs=3857, scheme="tms")
        xyz = latlon_to_tile(zoom=6, lat=web_mercator_pos[1], lng=web_mercator_pos[0], source_crs=3857, scheme="xyz")
        self.assertEqual((33, 41), tms)
        self.assertEqual((33, 22), xyz)

    def test_get_zoom_by_scale_min(self):
        zoom = get_zoom_by_scale(-1)
        self.assertEqual(23, zoom)

    def test_get_zoom_by_scale_max(self):
        zoom = get_zoom_by_scale(10000000000)
        self.assertEqual(0, zoom)

    def test_get_zoom_by_scale(self):
        zoom = get_zoom_by_scale(12500)
        self.assertEqual(14, zoom)

    def test_get_epsg(self):
        self.assertEqual(3857, get_code_from_epsg("epsg:3857"))

    def test_world_bounds(self):
        tile = get_tile_bounds(zoom=14, extent=WORLD_BOUNDS, source_crs=4326, scheme="xyz")
        bounds_expected = Bounds(
            y_min=0,
            y_max=16383,
            zoom=14,
            x_max=16383,
            x_min=0,
            scheme="xyz"
        )
        
        self.assertEqual(bounds_expected, tile)

    def test_center_zero_limit(self):
        all_tiles = list(itertools.product(range(1, 6), range(1, 6)))
        t = get_tiles_from_center(nr_of_tiles=0, available_tiles=all_tiles)
        self.assertEqual(0, len(t))

    def test_center_tiles_high_limit(self):
        all_tiles = list(itertools.product(range(1, 6), range(1, 6)))
        t = get_tiles_from_center(nr_of_tiles=26, available_tiles=all_tiles)
        self.assertEqual(25, len(t))

    def test_center_tiles_cancel(self):
        all_tiles = list(itertools.product(range(1, 6), range(1, 6)))
        t = get_tiles_from_center(nr_of_tiles=5, available_tiles=all_tiles, should_cancel_func=lambda: True)
        self.assertEqual(1, len(t))

    def test_center_tiles_equality(self):
        tile_limit = 4
        extent_a = Bounds(y_min=3, y_max=5, zoom=3, x_max=4, x_min=3, scheme="xyz")
        extent_b = Bounds(y_min=3, y_max=6, zoom=3, x_max=7, x_min=0, scheme="xyz")
        tiles_equal = center_tiles_equal(tile_limit=tile_limit, extent_a=extent_a, extent_b=extent_b)
        self.assertTrue(tiles_equal)


def suite():
    s = unittest.makeSuite(TileHelperTests, "test")
    return s


# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())


if __name__ == "__main__":
    run_all()
