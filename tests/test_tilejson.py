import unittest
from util.tile_helper import get_tile_bounds, tile_to_latlon, WORLD_BOUNDS
from util.tile_json import TileJSON


class TileJsonTests(unittest.TestCase):
    """
    Tests for Iface
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_load(self):
        tj = _get_loaded()
        assert tj.json

    def test_bounds(self):
        tj = _get_loaded()
        b = tj.bounds_longlat()
        self.assertIsNotNone(b)
        self.assertEqual(4, len(b))

    def test_tile_to_latlon(self):
        latlon = tile_to_latlon(14, 8568, 5747, scheme="xyz")
        latlon_expected = (919690.3243272416, 5977987.108127065, 922136.3092323653, 5980433.093032189)
        self.assertEqual(latlon_expected, latlon)

    def test_manual_bounds_xyz(self):
        # boundary for mbtiles zurich 4 tiles in bottom left corner
        b = [8.268328, 47.222658, 8.298712, 47.243988]
        t = get_tile_bounds(14, b, scheme="xyz", source_crs=4326)
        bounds_expected = {
            "x_min": 8568,
            "y_min": 5746,
            "x_max": 8569,
            "y_max": 5747,
            "zoom": 14,
            "width": 2,
            "height": 2,
            "scheme": "xyz"
        }
        self.assertEqual(bounds_expected, t)

    def test_manual_bounds_tms(self):
        # boundary for mbtiles zurich 4 tiles in bottom left corner
        b = [8.268328, 47.222658, 8.298712, 47.243988]
        t = get_tile_bounds(14, b, scheme="tms", source_crs=4326)
        bounds_expected = {
            "x_min": 8568,
            "y_min": 10636,
            "x_max": 8569,
            "y_max": 10637,
            "zoom": 14,
            "width": 2,
            "height": 2,
            "scheme": "tms"
        }
        self.assertIsNotNone(t)
        self.assertEqual(bounds_expected, t)

    def test_tile_bounds_world(self):
        tj = _get_loaded()
        b = tj.bounds_tile(14)
        bounds_expected = {
            "x_min": 0,
            "y_min": 0,
            "x_max": 16383,
            "y_max": 16383,
            "zoom": 14,
            "width": 16384,
            "height": 16384,
            "scheme": "xyz"
        }
        self.assertIsNotNone(b)
        self.assertEqual(bounds_expected, b)

    def test_no_bounds(self):
        js = {
            "scheme": "xyz"
        }

        tj = _get_loaded(js)
        b = tj.bounds_tile(14)
        self.assertIsNotNone(b)
        world_bounds_tile = get_tile_bounds(zoom=14, source_crs=4326, scheme="xyz", extent=WORLD_BOUNDS)
        self.assertEqual(world_bounds_tile, b)


def _get_loaded(json=None):
    tj = TileJSON("")
    if json:
        tj.json = json
    else:
        tj.json = _get_test_tilejson()
    return tj


def _get_test_tilejson():
    return {
        "tiles": ["https://free-0.tilehosting.com/data/v3/{z}/{x}/{y}.pbf.pict?key=GiVhgsc1enVLFVtuIdLT", "https://free-1.tilehosting.com/data/v3/{z}/{x}/{y}.pbf.pict?key=GiVhgsc1enVLFVtuIdLT", "https://free-2.tilehosting.com/data/v3/{z}/{x}/{y}.pbf.pict?key=GiVhgsc1enVLFVtuIdLT", "https://free-3.tilehosting.com/data/v3/{z}/{x}/{y}.pbf.pict?key=GiVhgsc1enVLFVtuIdLT"],
        "name": "OpenMapTiles",
        "format": "pbf",
        "basename": "v3.5.mbtiles",
        "id": "openmaptiles",
        "attribution": "<a href=\"http://www.openmaptiles.org/\" target=\"_blank\">&copy; OpenMapTiles</a> <a href=\"http://www.openstreetmap.org/about/\" target=\"_blank\">&copy; OpenStreetMap contributors</a>",
        "center": [-12.2168, 28.6135, 4],
        "description": "A tileset showcasing all layers in OpenMapTiles. http://openmaptiles.org",
        "maxzoom": 14,
        "minzoom": 0,
        "version": "3.5",
        "bounds": WORLD_BOUNDS,
        "maskLevel": "8",
        "planettime": "1491177600000",
        "tilejson": "2.0.0",
        "vector_layers": [{
                "maxzoom": 14,
                "fields": {
                    "class": "String"
                },
                "minzoom": 0,
                "id": "water",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "name_en": "String",
                    "name": "String",
                    "name_de": "String",
                    "class": "String"
                },
                "minzoom": 0,
                "id": "waterway",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "class": "String",
                    "subclass": "String"
                },
                "minzoom": 0,
                "id": "landcover",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "class": "String"
                },
                "minzoom": 0,
                "id": "landuse",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "name": "String",
                    "osm_id": "Number",
                    "rank": "Number",
                    "ele": "Number",
                    "name_de": "String",
                    "ele_ft": "Number",
                    "name_en": "String"
                },
                "minzoom": 0,
                "id": "mountain_peak",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "class": "String"
                },
                "minzoom": 0,
                "id": "park",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "admin_level": "Number",
                    "disputed": "Number",
                    "maritime": "Number"
                },
                "minzoom": 0,
                "id": "boundary",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "class": "String"
                },
                "minzoom": 0,
                "id": "aeroway",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "brunnel": "String",
                    "ramp": "Number",
                    "class": "String",
                    "service": "String",
                    "oneway": "Number"
                },
                "minzoom": 0,
                "id": "transportation",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "render_min_height": "Number",
                    "render_height": "Number"
                },
                "minzoom": 0,
                "id": "building",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "name_en": "String",
                    "name": "String",
                    "name_de": "String",
                    "class": "String"
                },
                "minzoom": 0,
                "id": "water_name",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "name": "String",
                    "ref_length": "Number",
                    "name_de": "String",
                    "name_en": "String",
                    "ref": "String",
                    "class": "String",
                    "network": "String"
                },
                "minzoom": 0,
                "id": "transportation_name",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "name": "String",
                    "rank": "Number",
                    "name_de": "String",
                    "capital": "Number",
                    "name_en": "String",
                    "class": "String"
                },
                "minzoom": 0,
                "id": "place",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "housenumber": "String"
                },
                "minzoom": 0,
                "id": "housenumber",
                "description": ""
            }, {
                "maxzoom": 14,
                "fields": {
                    "name": "String",
                    "rank": "Number",
                    "name_de": "String",
                    "subclass": "String",
                    "name_en": "String",
                    "class": "String"
                },
                "minzoom": 0,
                "id": "poi",
                "description": ""
            }
        ]
    }
