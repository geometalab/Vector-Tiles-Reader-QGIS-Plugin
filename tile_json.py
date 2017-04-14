import sys
import urllib2
import json
from log_helper import critical, debug
from tile_helper import get_tile_bounds

class TileJSON:
    """
     * Wrapper for TileJSON v2.2.0
     * https://github.com/mapbox/tilejson-spec/tree/master/2.2.0
    """
    def __init__(self, url):
        self.url = url
        self.json = None

    def load(self):
        self._set_debug_json()
        return True

        success = False
        try:
            response = urllib2.urlopen(self.url)
            data = response.read()
            self.json = json.loads(data)
            debug("TileJSON loaded: {}", self.json)
            success = True
        except urllib2.HTTPError as e:
            critical("HTTP error {}: {}", e.code, e.message)
        except:
            critical("Loading TileJSON failed ({}): {}", self.url, sys.exc_info())
        return success

    def bounds_longlat(self):
        bounds = self._get_value("bounds", is_array=True)
        if bounds:
            assert len(bounds) == 4
        return bounds

    def bounds_tile(self, zoom):
        """
         * Returns the tile boundaries in the form [(x_min, y_min), (x_max, y_max)] where both values are tuples
        :param zoom: 
        :param manual_bounds: 
        :return:         """

        bounds = self.bounds_longlat()
        return get_tile_bounds(zoom, bounds)

    def vector_layers(self):
        layers = self._get_value("vector_layers", is_array=True, is_required=True)
        return layers

    def tiles(self):
        tiles = self._get_value("tiles", is_array=True, is_required=True)
        return tiles

    def min_zoom(self):
        min_zoom = self._get_value("minzoom")
        return min_zoom

    def max_zoom(self):
        max_zoom = self._get_value("maxzoom")
        return max_zoom

    def _get_value(self, field_name, is_array=False, is_required=False):
        if is_required and not field_name in self.json:
            raise RuntimeError("The field '{}' is required but not found. This is invalid TileJSON.".format(field_name))

        result = None
        if field_name in self.json:
            if is_array:
                result = []
                result.extend(self.json[field_name])
                if is_required and len(result) == 0:
                    raise RuntimeError("The field '{}' is required but is empty. At least one entry is expected.".format(field_name))
            else:
                result = self.json[field_name]
        return result

    def _set_debug_json(self):
        self.json = {
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
