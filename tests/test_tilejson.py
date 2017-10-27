from tile_json import TileJSON
import pytest
from tile_helper import get_tile_bounds, latlon_to_tile, epsg3857_to_wgs84_lonlat, tile_to_latlon

def test_load():
    tj = _get_loaded()
    assert tj.json

def test_bounds():
    tj = _get_loaded()
    b = tj.bounds_longlat()
    assert b
    assert len(b) == 4

def test_tile_to_latlon():
    latlon = tile_to_latlon(14, 8568, 5747, scheme="xyz")
    assert latlon == (919690.3243272416, 5977987.108127065, 922136.3092323653, 5980433.093032189)

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
    b = latlon_to_tile(14, 47.22541, 8.27173)  # hitzkirch coordinates
    assert b
    assert b[0] == 8568
    assert b[1] == 5747

def test_tile_bounds_world():
    tj = _get_loaded()
    b = tj.bounds_tile(14)
    b_min = b[0]
    b_max = b[1]
    print b
    assert b
    assert b_min == (-1, -1)
    assert b_max == (16383, 16383)

def test_center_tile():
    json = {
        "center": [8.27187, 47.22550, 14],
        "scheme": "xyz"
    }
    tj = _get_loaded(json)
    center = tj.center_tile()
    print center
    assert center == (8568, 5747)

def test_center_tile_from_bounds():
    json = {
        "maxzoom": 14,
        "bounds": [8.27187, 47.22550, 8.30261, 47.22183],
        "scheme": "xyz"
    }
    tj = _get_loaded(json)
    center = tj.center_tile()
    assert center == (8568, 5747)

def _get_loaded(json=None):
    tj = TileJSON("")
    if json:
        tj.json = json
    else:
        tj.json = _get_test_tilejson()
    return tj

def test_epsg3857towgs84():
    a = [915107.5592417066, 5977040.352606636]
    b = epsg3857_to_wgs84_lonlat(a[0], a[1])
    assert b == [8.220551070801354, 47.21379138314561]

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
        "bounds": [-180, -85.0511, 180, 85.0511],
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
