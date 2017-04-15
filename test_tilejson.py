from tile_json import TileJSON
import pytest
from tile_helper import get_tile_bounds, coordinate_to_tile

def test_load():
    tj = _get_loaded()
    assert tj.json

def test_bounds():
    tj = _get_loaded()
    b = tj.bounds_longlat()
    assert b
    assert len(b) == 4

def test_manual_bounds_xyz():
    # boundary for mbtiles zurich 4 tiles in bottom left corner
    b = [8.268328, 47.222658, 8.298712, 47.243988]
    t = get_tile_bounds(14, b, scheme="xyz")
    assert t[0] == (8568, 5746)
    assert t[1] == (8569, 5747)

def test_manual_bounds_tms():
    # boundary for mbtiles zurich 4 tiles in bottom left corner
    b = [8.268328, 47.222658, 8.298712, 47.243988]
    t = get_tile_bounds(14, b, scheme="tms")
    assert t[0] == (8568, 10637)
    assert t[1] == (8569, 10636)

def test_tile_bounds():
    b = coordinate_to_tile(14, 47.22541, 8.27173)  # hitzkirch coordinates
    assert b
    assert b[0] == 8568
    assert b[1] == 5747

def test_tile_bounds_world():
    tj = _get_loaded()
    b = tj.bounds_tile(14)
    b_min = b[0]
    b_max = b[1]
    assert b
    assert b_min == (-1, -1)
    assert b_max == (16383, 16383)

def _get_loaded():
    tj = TileJSON("")
    tj.json = _get_test_tilejson()
    return tj

def _get_test_tilejson():
    return {
            "attribution": "<a href=\"http://www.openmaptiles.org/\" target=\"_blank\">&copy; OpenMapTiles</a> <a href=\"http://www.openstreetmap.org/about/\" target=\"_blank\">&copy; OpenStreetMap contributors</a>",
            "bounds": [-180, -85.05112877980659, 180, 85.0511287798066],
            "center": [5.9290021, 1.6631951, 4],
            "created": 1484041965082,
            "description": "A tileset showcasing all layers in OpenMapTiles. http://openmaptiles.org. Switzerland in EPSG:21781",
            "filesize": 163278848,
            "format": "pbf",
            "id": "openmaptiles.c69qy1yd",
            "mapbox_logo": True,
            "maxzoom": 14,
            "minzoom": 0,
            "modified": 1484041964729,
            "name": "20161214-dn68t9",
            "private": False,
            "scheme": "xyz",
            "tilejson": "2.2.0",
            "tiles": ["https://a.tiles.mapbox.com/v4/openmaptiles.c69qy1yd/{z}/{x}/{y}.vector.pbf?access_token=pk.eyJ1Ijoib3Blbm1hcHRpbGVzIiwiYSI6ImNpdnY3eTJxZzAwMGMyb3BpdWJmajcxNzcifQ.hP1BxcxldIhakMcPSJLQ1Q", "https://b.tiles.mapbox.com/v4/openmaptiles.c69qy1yd/{z}/{x}/{y}.vector.pbf?access_token=pk.eyJ1Ijoib3Blbm1hcHRpbGVzIiwiYSI6ImNpdnY3eTJxZzAwMGMyb3BpdWJmajcxNzcifQ.hP1BxcxldIhakMcPSJLQ1Q"],
            "vector_layers": [{
                    "description": "",
                    "fields": {
                        "class": "String"
                    },
                    "id": "water",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "class": "String",
                        "name": "String"
                    },
                    "id": "waterway",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "class": "String",
                        "subclass": "String"
                    },
                    "id": "landcover",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "class": "String"
                    },
                    "id": "landuse",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "class": "String"
                    },
                    "id": "park",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "admin_level": "Number"
                    },
                    "id": "boundary",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "class": "String"
                    },
                    "id": "aeroway",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "brunnel": "String",
                        "class": "String",
                        "oneway": "Number",
                        "ramp": "Number",
                        "service": "String"
                    },
                    "id": "transportation",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "render_height": "Number",
                        "render_min_height": "Number"
                    },
                    "id": "building",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "class": "String",
                        "name": "String",
                        "name_en": "String"
                    },
                    "id": "water_name",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "class": "String",
                        "name": "String",
                        "ref": "String",
                        "ref_length": "Number"
                    },
                    "id": "transportation_name",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "capital": "Number",
                        "class": "String",
                        "name": "String",
                        "name_en": "String",
                        "rank": "Number"
                    },
                    "id": "place",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "housenumber": "String"
                    },
                    "id": "housenumber",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }, {
                    "description": "",
                    "fields": {
                        "class": "String",
                        "name": "String",
                        "name_en": "String",
                        "rank": "Number",
                        "subclass": "String"
                    },
                    "id": "poi",
                    "maxzoom": 14,
                    "minzoom": 0,
                    "source": "openmaptiles.c69qy1yd",
                    "source_name": "20161214-dn68t9"
                }
            ],
            "version": "1.0.0",
            "webpage": "https://a.tiles.mapbox.com/v4/openmaptiles.c69qy1yd/page.html?access_token=pk.eyJ1Ijoib3Blbm1hcHRpbGVzIiwiYSI6ImNpdnY3eTJxZzAwMGMyb3BpdWJmajcxNzcifQ.hP1BxcxldIhakMcPSJLQ1Q"
        }
