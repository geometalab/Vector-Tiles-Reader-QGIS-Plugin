import sys
import json
from log_helper import critical, debug
from tile_helper import get_tile_bounds
from file_helper import FileHelper

class TileJSON:
    """
     * Wrapper for TileJSON v2.2.0
     * https://github.com/mapbox/tilejson-spec/tree/master/2.2.0
    """
    def __init__(self, url):
        self.url = url
        self.json = None

    def load(self):
        debug("Loading TileJSON")
        success = False
        try:
            data = FileHelper.load_url(self.url)
            self.json = json.loads(data)
            if self.json:
                debug("TileJSON loaded")
                success = True
            else:
                debug("Loading TileJSON failed")
        except:
            print("error")
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

        #todo: return named dict instead with x_min, x_max, y_min, y_max
        bounds = self.bounds_longlat()
        scheme = self.scheme()
        return get_tile_bounds(zoom, bounds, scheme)

    def vector_layers(self):
        layers = self._get_value("vector_layers", is_array=True, is_required=True)
        return layers

    def crs(self):
        crs = self._get_value("crs")
        if not crs:
            crs = self._get_value("srs")
        return crs

    def scheme(self, default="xyz"):
        scheme = self._get_value("scheme")
        if not scheme:
            scheme = default
        return scheme

    def tiles(self):
        tiles = self._get_value("tiles", is_array=True, is_required=True)
        return tiles

    def id(self):
        return self._get_value("id")

    def min_zoom(self):
        min_zoom = self._get_value("minzoom")
        return min_zoom

    def max_zoom(self):
        max_zoom = self._get_value("maxzoom")
        return max_zoom

    def mask_level(self):
        return self._get_value("maskLevel")

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