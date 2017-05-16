import sys
import json
from log_helper import critical, debug
from tile_helper import get_tile_bounds, coordinate_to_tile
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
            status, data = FileHelper.load_url(self.url)
            self.json = json.loads(data)
            if self.json:
                debug("TileJSON loaded")
                self._validate()
                success = True
            else:
                debug("Loading TileJSON failed")
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
            center = coordinate_to_tile(zoom, lat, lng, self.crs(), self.scheme())
        else:
            center = self.bounds_tile(self.max_zoom())
            if center:
                min_x = center[0][0]
                min_y = center[0][1]
                max_x = center[1][0]
                max_y = center[1][1]
                center_x = int((min_x + max_x) / 2)
                center_y = int((min_y + max_y) / 2)
                center = (center_x, center_y)
        return center

    def attribution(self):
        return self._get_value("attribution")

    def center_longlat(self):
        return self._get_value("center")

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

        # todo: return named dict instead with x_min, x_max, y_min, y_max
        bounds = self.bounds_longlat()
        scheme = self.scheme()
        crs = self.crs()
        return get_tile_bounds(zoom, bounds, crs, scheme)

    def vector_layers(self):
        layers = self._get_value("vector_layers", is_array=True, is_required=True)
        return layers

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

    def is_within_bounds(self, zoom, extent):
        bounds = self.bounds_tile(zoom)
        is_within = True
        if bounds:
            x_min_within = extent[0][0] >= bounds[0][0]
            y_min_within = extent[0][1] >= bounds[0][1]
            x_max_within = extent[1][0] <= bounds[1][0]
            y_max_within = extent[1][1] <= bounds[1][1]
            is_within = x_min_within and y_min_within and x_max_within and y_max_within
            debug("Extent {} is within bounds {}: {}", extent, bounds, is_within)
        else:
            debug("Assuming extent is within bounds")
        return is_within

    def _get_value(self, field_name, is_array=False, is_required=False):
        if not self.json or (is_required and field_name not in self.json):
            raise RuntimeError("The field '{}' is required but not found. This is invalid TileJSON.".format(field_name))

        result = None
        if field_name in self.json:
            if is_array:
                result = []
                result.extend(self.json[field_name])
                if is_required and len(result) == 0:
                    raise RuntimeError(
                        "The field '{}' is required but is empty. At least one entry is expected.".format(field_name))
            else:
                result = self.json[field_name]
        return result
