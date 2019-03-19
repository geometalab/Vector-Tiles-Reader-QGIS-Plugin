import ast
import os
import sys
from typing import List, Optional, Tuple

from .log_helper import critical, debug, info
from .network_helper import http_get
from .tile_helper import WORLD_BOUNDS, get_tile_bounds

try:
    import simplejson as json
except ImportError:
    import json


class TileJSON(object):
    """
     * Wrapper for TileJSON v2.2.0
     * https://github.com/mapbox/tilejson-spec/tree/master/2.2.0
    """

    def __init__(self, url: str):
        self.url = url
        self.json: Optional[dict] = None

    def load(self) -> bool:
        debug("Loading TileJSON")
        success = False
        try:
            if os.path.isfile(self.url):
                with open(self.url, "r") as f:
                    data = f.read()
            else:
                status, data = http_get(self.url)
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

    def _validate(self) -> None:
        bounds = self.bounds_longlat()
        center = self.center_longlat()
        if not bounds and not center:
            raise RuntimeError("Either 'bounds' or 'center' MUST be available in the TileJSON for the plugin to work")

    def attribution(self) -> str:
        return self._get_value("attribution")

    def center_longlat(self) -> List[float]:
        return self._get_value("center", is_array=True)

    def bounds_longlat(self) -> Tuple[float, float, float, float]:
        bounds = self._get_value("bounds", is_array=True)
        if bounds:
            assert len(bounds) == 4
        else:
            bounds = WORLD_BOUNDS
        return bounds

    def bounds_tile(self, zoom: int) -> dict:
        """
         * Returns the tile boundaries in the form [(x_min, y_min), (x_max, y_max)] where both values are tuples
        :param zoom: 
        :return:         """
        bounds = self.bounds_longlat()
        scheme = self.scheme()
        tile_bounds = get_tile_bounds(zoom=zoom, extent=bounds, scheme=scheme, source_crs="EPSG:4326")
        return tile_bounds

    def vector_layers(self) -> List[dict]:
        layers = self._get_value("vector_layers", is_array=True, is_required=True)
        return layers

    def get_value(self, key: str, is_array: bool = False, is_required: bool = False):
        val = self._get_value(key, is_array=is_array, is_required=is_required)
        return val

    def crs(self, default: int = 3857) -> str:
        crs: str = self._get_value("crs")
        if not crs:
            crs = self._get_value("srs")
        if not crs:
            crs = str(default)
        return crs

    def scheme(self, default="xyz") -> str:
        scheme = self._get_value("scheme")
        if not scheme:
            scheme = default
        return scheme

    def tiles(self) -> List[str]:
        """
        Returns a list containing at one or more urls to the .pbf files
        :return:
        """

        tiles = self._get_value("tiles", is_array=True, is_required=True)
        return tiles

    def name(self) -> str:
        return self._get_value("name")

    def id(self) -> str:
        return self._get_value("id")

    def min_zoom(self) -> Optional[int]:
        min_zoom: str = self._get_value("minzoom")
        if min_zoom is not None:
            return int(min_zoom)
        return None

    def max_zoom(self) -> Optional[int]:
        max_zoom: str = self._get_value("maxzoom")
        if max_zoom is not None:
            return int(max_zoom)
        return None

    def _get_value(self, field_name: str, is_array: bool = False, is_required: bool = False):
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
                        "The field '{}' is required but is empty. At least one entry is expected.".format(field_name)
                    )
            else:
                result = self.json[field_name]
        return result
