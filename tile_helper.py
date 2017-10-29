from __future__ import division
from builtins import str
from builtins import map
from builtins import range
from past.utils import old_div
from builtins import object
from global_map_tiles import GlobalMercator
from osgeo import osr
import operator
from log_helper import warn, debug


class VectorTile(object):
    
    decoded_data = None

    def __init__(self, scheme, zoom_level, x, y):
        self.scheme = scheme
        self.zoom_level = int(zoom_level)
        self.column = int(x)
        self.row = int(y)
        self.extent = tile_to_latlon(self.zoom_level, self.column, self.row, self.scheme)
    
    def __str__(self):
        return "Tile (zoom={}, col={}, row={}".format(self.zoom_level, self.column, self.row)

    def id(self):
        return "{};{}".format(self.column, self.row)

    def coord(self):
        return self.column, self.row


def clamp(value, low=None, high=None):
    if low is not None and value < low:
        value = low
    if high is not None and value > high:
        value = high
    return value


def clamp_bounds(bounds_to_clamp, clamp_values):
    x_min = clamp(bounds_to_clamp["x_min"], low=clamp_values["x_min"])
    y_min = clamp(bounds_to_clamp["y_min"], low=clamp_values["y_min"])
    x_max = clamp(bounds_to_clamp["x_max"], high=clamp_values["x_max"])
    y_max = clamp(bounds_to_clamp["y_max"], high=clamp_values["y_max"])
    return create_bounds(bounds_to_clamp["zoom"], x_min, x_max, y_min, y_max)


def extent_overlap_bounds(extent, bounds):
    return (bounds["x_min"] <= extent["x_min"] <= bounds["x_max"] or
            bounds["x_min"] <= extent["x_max"] <= bounds["x_max"]) and\
            (bounds["y_min"] <= extent["y_min"] <= bounds["y_max"] or
             bounds["y_min"] <= extent["y_max"] <= bounds["y_max"])


def create_bounds(zoom, x_min, x_max, y_min, y_max):
    return {
        "zoom": int(zoom),
        "x_min": int(x_min),
        "x_max": int(x_max),
        "y_min": int(y_min),
        "y_max": int(y_max),
        "width": int(x_max - x_min + 1),
        "height": int(y_max - y_min + 1)
    }


def latlon_to_tile(zoom, lat, lng, scheme="xyz"):
    """
     * Returns the tile-xy from the specified WGS84 lat/long coordinates
    :param zoom:
    :param lat:
    :param lng:
    :return:
    """
    if zoom is None:
        raise RuntimeError("zoom is required")
    if lat is None:
        raise RuntimeError("latitude is required")
    if lng is None:
        raise RuntimeError("Longitude is required")

    max_lat = 85.05112878
    max_lng = 180
    lat = clamp(lat, -max_lat, max_lat)
    lng = clamp(lng, -max_lng, max_lng)

    gm = GlobalMercator()
    m = gm.LatLonToMeters(lat, lng)
    tile = gm.MetersToTile(m[0], m[1], zoom)
    x = clamp(tile[0], low=0)
    y = tile[1]
    if scheme != "tms":
        y = change_scheme(zoom, y)
    y = clamp(y, low=0)
    return int(x), int(y)


def convert_coordinate(source_crs, target_crs, lat, lng):
    source_crs = get_code_from_epsg(source_crs)
    target_crs = get_code_from_epsg(target_crs)

    src = osr.SpatialReference()
    tgt = osr.SpatialReference()
    src.ImportFromEPSG(source_crs)
    tgt.ImportFromEPSG(target_crs)
    transform = osr.CoordinateTransformation(src, tgt)
    return transform.TransformPoint(lng, lat)


def get_code_from_epsg(epsg_string):
    code = str(epsg_string).upper()
    if code.startswith("EPSG:"):
        code = code.replace("EPSG:", "")
    return int(code)


def epsg3857_to_wgs84_lonlat(x, y):
    wgs84 = convert_coordinate(3857, 4326, x, y)
    return wgs84[1], wgs84[0]


def tile_to_latlon(zoom, x, y, scheme="tms"):
    """
     * Returns the tile extent in ESPG:3857 coordinates
    :param zoom: 
    :param x: 
    :param y: 
    :param scheme: 
    :return: 
    """

    gm = GlobalMercator()
    if scheme != "tms":
        y = change_scheme(zoom, y)
    return gm.TileBounds(x, y, zoom)


def get_tile_bounds(zoom, bounds, scheme="xyz"):
    """
     * Returns the tile boundaries in XYZ scheme in the form [(x_min, y_min), (x_max, y_max)] where both values are tuples
    :param scheme: 
    :param zoom: 
    :param bounds: 
    :return: 
    """
    if scheme not in ["xyz", "tms"]:
        raise RuntimeError("Scheme not supported: {}".format(scheme))
    if not bounds:
        warn("Bounds is not available")
    tile_bounds = None
    if bounds:
        lng_min = bounds[0]
        lat_min = bounds[1]
        lng_max = bounds[2]
        lat_max = bounds[3]

        xy_min = latlon_to_tile(zoom, lat_max, lng_min, scheme)
        xy_max = latlon_to_tile(zoom, lat_min, lng_max, scheme)

        x_min = int(min(xy_min[0], xy_max[0]))
        x_max = int(max(xy_min[0], xy_max[0]))
        y_min = int(min(xy_min[1], xy_max[1]))
        y_max = int(max(xy_min[1], xy_max[1]))

        tile_bounds = create_bounds(zoom, x_min, x_max, y_min, y_max)
    return tile_bounds


def change_zoom(source_zoom, target_zoom, tile, scheme):
    """
    * Converts tile coordinates from one zoom-level to another
    :param source_zoom: 
    :param target_zoom: 
    :param tile: 
    :param scheme: 
    :return:
    """
    lat_lon = tile_to_latlon(source_zoom, tile[0], tile[1], scheme)
    new_tile = latlon_to_tile(target_zoom, lat_lon[1], lat_lon[0], scheme)
    return new_tile


def get_all_tiles(bounds, is_cancel_requested_handler):
    tiles = []
    width = bounds["width"]
    height = bounds["height"]
    x_min = bounds["x_min"]
    y_min = bounds["y_min"]
    debug("Preprocessing {} tiles", width*height)
    for x in range(width):
        if is_cancel_requested_handler():
            break
        for y in range(height):
            col = x + x_min
            row = y + y_min
            tiles.append((col, row))
    return tiles


def change_scheme(zoom, y):
    """
     * Transforms the y coordinate (row) from TMS scheme to XYZ scheme and vice-versa
    :param zoom: 
    :param y: 
    :return: 
    """
    return (2 ** zoom) - y - 1

_UP = 0
_RIGHT = 1
_DOWN = 2
_LEFT = 3

_directions = {
    _UP: (0, -1),
    _RIGHT: (1, 0),
    _DOWN: (0,1),
    _LEFT: (-1, 0)
    }


def get_tiles_from_center(nr_of_tiles, available_tiles, should_cancel_func):
    if nr_of_tiles > len(available_tiles):
        nr_of_tiles = len(available_tiles)

    debug("Getting {} center-tiles from a total of {} tiles", nr_of_tiles, len(available_tiles))
    if not nr_of_tiles or nr_of_tiles >= len(available_tiles) or len(available_tiles) == 0:
        return available_tiles

    min_x = min([t[0] for t in available_tiles])
    min_y = min([t[1] for t in available_tiles])
    max_x = max([t[0] for t in available_tiles])
    max_y = max([t[1] for t in available_tiles])

    center_tile_offset = (int(round(old_div((max_x-min_x),2))), int(round(old_div((max_y-min_y),2))))
    selected_tiles = set()
    center_tile = _sum_tiles((min_x, min_y), center_tile_offset)
    if center_tile in available_tiles:
        selected_tiles.add(center_tile)

    current_tile = center_tile
    nr_of_steps = 0
    current_direction = 0
    while len(selected_tiles) < nr_of_tiles:
        if should_cancel_func and should_cancel_func():
            break

        #  always after two direction changes, the step length has to be increased by one
        if current_direction % 2 == 0:
            nr_of_steps += 1

        #  go nr_of_steps steps into the current direction
        for s in range(nr_of_steps):
            current_tile = _sum_tiles(current_tile, _directions[current_direction])
            if current_tile in available_tiles:
                selected_tiles.add(current_tile)
                if len(selected_tiles) >= nr_of_tiles:
                    break
        current_direction = (current_direction + 1) % 4
    debug("Center tiles completed")
    return selected_tiles


def _sum_tiles(first_tile, second_tile):
    return tuple(map(operator.add, first_tile, second_tile))


def get_zoom_by_scale(scale):
    if scale < 0:
        scale = 0
    zoom = 0
    for lower_bound in sorted(_zoom_level_by_lower_scale_bound, key=lambda k: k*-1):
        if scale >= lower_bound:
            zoom = _zoom_level_by_lower_scale_bound[lower_bound]
            break
    return zoom


_zoom_level_by_lower_scale_bound = {
    1000000000: 0,
    500000000: 1,
    200000000: 2,
    50000000: 3,
    25000000: 4,
    12500000: 5,
    6500000: 6,
    3000000: 7,
    1500000: 8,
    750000: 9,
    400000: 10,
    200000: 11,
    100000: 12,
    50000: 13,
    25000: 14,
    12500: 15,
    5000: 16,
    2500: 17,
    1500: 18,
    750: 19,
    500: 20,
    250: 21,
    100: 22,
    0: 23
}
