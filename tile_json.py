from __future__ import division
from builtins import str
from builtins import object
from past.utils import old_div
import sys
import json
import os
import ast
from log_helper import critical, debug, info
from tile_helper import get_tile_bounds, latlon_to_tile
from network_helper import load_url


class TileJSON(object):
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
            if os.path.isfile(self.url):
                with open(self.url, 'r') as f:
                    data = f.read()
            else:
                status, data = load_url(self.url)
            self.json = json.loads(data)
            if self.json:
                debug("TileJSON loaded")
                self._validate()
                debug("TileJSON validated")
                success = True
            else:
                info("Parsing TileJSON failed")
                self.json = {}
                raise RuntimeError("TileJSON could not be loaded.")
        except:
            critical("Loading TileJSON failed ({}): {}", self.url, sys.exc_info())
        return success

    def _validate(self):
        bounds = self.bounds_longlat()
        center = self.center_longlat()
        if not bounds and not center:
            raise RuntimeError("Either 'bounds' or 'center' MUST be available in the TileJSON for the plugin to work")

    def center_tile(self):
        """
         * Returns the center of the available data. If the 'center' value is not available in the TileJSON,
         * the center is calculated from the bounds. That means either 'center' or 'bounds' is required in the json.
        :return: 
        """

        center = self.center_longlat()
        if center:
            assert len(center) == 3
            lng = center[0]
            lat = center[1]
            zoom = center[2]
            center = latlon_to_tile(zoom, lat, lng, self.scheme())
        else:
            bounds = self.bounds_tile(self.max_zoom())
            if bounds:
                center_x = int(old_div((bounds["x_min"] + bounds["x_max"]), 2))
                center_y = int(old_div((bounds["y_min"] + bounds["y_max"]), 2))
                center = (center_x, center_y)
        return center

    def attribution(self):
        return self._get_value("attribution")

    def center_longlat(self):
        return self._get_value("center", is_array=True)

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
        scheme = self.scheme()
        return get_tile_bounds(zoom=zoom, bounds=bounds, scheme=scheme)

    def vector_layers(self):
        layers = self._get_value("vector_layers", is_array=True, is_required=True)
        return layers

    def get_value(self, key):
        val = self._get_value(key)
        return val

    def crs(self, default="EPSG:3857"):
        crs = self._get_value("crs")
        if not crs:
            crs = self._get_value("srs")
        if not crs:
            crs = default
        return crs

    def scheme(self, default="xyz"):
        scheme = self._get_value("scheme")
        if not scheme:
            scheme = default
        return scheme

    def tiles(self):
        tiles = self._get_value("tiles", is_array=True, is_required=True)
        return tiles

    def name(self):
        return self._get_value("name")

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
        if not self.json or (is_required and field_name not in self.json):
            raise RuntimeError("The field '{}' is required but not found. This is invalid TileJSON.".format(field_name))

        result = None
        if field_name in self.json:
            if is_array:
                result = []
                result_arr = ast.literal_eval(str(self.json[field_name]))
                result.extend(result_arr)
                if is_required and len(result) == 0:
                    raise RuntimeError(
                        "The field '{}' is required but is empty. At least one entry is expected.".format(field_name))
            else:
                result = self.json[field_name]
        return result
