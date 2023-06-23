import itertools
from math import floor, ceil
from typing import Callable, List, Optional, Tuple, TypeVar

from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsPointXY, QgsProject

from .global_map_tiles import GlobalMercator
from .log_helper import debug, info, warn

StrOrInt = TypeVar("StrOrInt", str, int)

"""
 * Top left: (lng=WORLD_BOUNDS[0], lat=WORLD_BOUNDS[3])
 * Bottom right: (lng=WORLD_BOUNDS[2], lat=WORLD_BOUNDS[1])
"""
WORLD_BOUNDS = (-180.0, -85.05112878, 180.0, 85.05112878)


class Bounds(dict):
    def __init__(self, zoom: int, x_min: int, x_max: int, y_min: int, y_max: int, scheme: str):
        super().__init__([])
        self["zoom"] = zoom
        self["x_min"] = x_min
        self["x_max"] = x_max
        self["y_min"] = y_min
        self["y_max"] = y_max
        self["width"] = x_max - x_min + 1
        self["height"] = y_max - y_min + 1
        self["scheme"] = scheme

    def zoom(self) -> int:
        return self["zoom"]

    def x_min(self) -> int:
        return self["x_min"]

    def x_max(self) -> int:
        return self["x_max"]

    def y_min(self) -> int:
        return self["y_min"]

    def y_max(self) -> int:
        return self["y_max"]

    def width(self) -> int:
        return self.x_max() - self.x_min() + 1

    def height(self) -> int:
        return self.y_max() - self.y_min() + 1

    def scheme(self) -> str:
        return self["scheme"]

    @classmethod
    def create(cls, zoom: int, x_min: int, x_max: int, y_min: int, y_max: int, scheme: str) -> "Bounds":
        return Bounds(zoom=zoom, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, scheme=scheme)


class VectorTile:
    decoded_data = {}

    def __init__(self, scheme, zoom_level, x, y):
        self.scheme = scheme
        self.zoom_level = int(zoom_level)
        self.column = int(x)
        self.row = int(y)
        self.extent = tile_to_latlon(self.zoom_level, self.column, self.row, self.scheme)

    def __str__(self):
        return "Tile ({}, {}, {})".format(self.zoom_level, self.column, self.row)

    def id(self):
        return "{};{}".format(self.column, self.row)

    def coord(self):
        return self.column, self.row


def clamp(value: Optional[int], low: Optional[int] = None, high: Optional[int] = None) -> Optional[int]:
    if low is not None and value < low:
        value = low
    if high is not None and value > high:
        value = high
    return value


def clamp_bounds(bounds_to_clamp: Bounds, clamp_values: Bounds) -> Bounds:
    assert bounds_to_clamp.zoom() == clamp_values.zoom()
    x_min = clamp(bounds_to_clamp.x_min(), low=clamp_values.x_min())
    y_min = clamp(bounds_to_clamp.y_min(), low=clamp_values.y_min())
    x_max = clamp(bounds_to_clamp.x_max(), low=x_min, high=clamp_values.x_max())
    y_max = clamp(bounds_to_clamp.y_max(), low=y_min, high=clamp_values.y_max())
    return Bounds.create(
        zoom=bounds_to_clamp.zoom(), x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, scheme=bounds_to_clamp.scheme()
    )


def extent_overlap_bounds(extent: Bounds, bounds: Bounds) -> bool:
    return (
            bounds.x_min() <= extent.x_min() <= bounds.x_max() or bounds.x_min() <= extent.x_max() <= bounds.x_max()
    ) and (bounds.y_min() <= extent.y_min() <= bounds.y_max() or bounds.y_min() <= extent.y_max() <= bounds.y_max())


def create_bounds(zoom: int, x_min: int, x_max: int, y_min: int, y_max: int, scheme: str) -> Bounds:
    return Bounds(zoom=zoom, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, scheme=scheme)


def center_tiles_equal(tile_limit: int, extent_a: Bounds, extent_b: Bounds) -> bool:
    center_tiles_a = _center_tiles(tile_limit=tile_limit, extent=extent_a)
    center_tiles_b = _center_tiles(tile_limit=tile_limit, extent=extent_b)
    return center_tiles_a == center_tiles_b


def _center_tiles(tile_limit: int, extent: Bounds):
    tiles = list(
        itertools.product(range(extent.x_min(), extent.x_max() + 1), range(extent.y_min(), extent.y_max() + 1))
    )
    center_tiles = get_tiles_from_center(nr_of_tiles=tile_limit, available_tiles=tiles)
    return center_tiles


def latlon_to_tile(zoom: int, lat: float, lng: float, source_crs: str, scheme="xyz") -> Tuple[int, int]:
    """
     * Returns the tile-xy from the specified WGS84 lat/long coordinates
    :param scheme: The tile scheme for which the tile coordinates shall be returned
    :param source_crs: The CRS in which lat/lon are represented
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

    if get_code_from_epsg(source_crs) != 3857:
        lng, lat = convert_coordinate(source_crs=source_crs, target_crs="epsg:3857", lat=lat, lng=lng)
    gm = GlobalMercator(tileSize=512)
    global_mercator_output_scheme = "tms"
    col, row = gm.MetersToTile(mx=lng, my=lat, zoom=zoom)  # GlobalMercator returns in TMS scheme here
    col = clamp(col, low=0)
    row = clamp(row, low=0)
    if scheme != global_mercator_output_scheme:
        row = clamp(change_scheme(zoom, row), low=0)

    return int(col), int(row)


def convert_coordinate(source_crs: StrOrInt, target_crs: StrOrInt, lat: float, lng: float) -> Tuple[float, float]:
    source_crs = get_code_from_epsg(source_crs)
    target_crs = get_code_from_epsg(target_crs)

    crs_src = QgsCoordinateReferenceSystem(source_crs)
    crs_dest = QgsCoordinateReferenceSystem(target_crs)
    xform = QgsCoordinateTransform(crs_src, crs_dest, QgsProject.instance())
    debug("CRS conversion, In: {} Out: {} Lon: {:.3f} Lat: {:.3f}", source_crs, target_crs, float(lng), float(lat))
    try:
        x, y = xform.transform(QgsPointXY(lng, lat))
    except:  # Handle infinity when caused for known reason
        shift = 0.001
        if lat != 90.0 and lng != 180.0:
            raise RuntimeError("Failed to solve CRS conversion exception: {} Out: {} Lon: {:.3f} Lat: {:.3f}".format(source_crs, target_crs, float(lng), float(lat)))
        else:
            x, y = xform.transform(QgsPointXY(lng - shift, lat - shift))
            warn("CRS conversion exception, applied shift to fix transform for In: {} Out: {} Lon: {:.3f} to {:.3f} Lat: {:.3f} to {:.3f} x: {:.3f} y: {:.3f}", source_crs, target_crs, float(lng), float(lng - shift), float(lat), float(lat - shift), x, y)

    return x, y


def get_code_from_epsg(epsg_string: StrOrInt) -> int:
    code = str(epsg_string).upper()
    if code.startswith("EPSG:"):
        code = code.replace("EPSG:", "")
    elif code.startswith("USER:"):
        code = code.replace("USER:", "")
    return int(code)


def tile_to_latlon(zoom: int, x: int, y: int, scheme: str = "tms") -> Tuple[float, float, float, float]:
    """
     * Returns the tile extent in ESPG:3857 coordinates
    :param zoom:
    :param x:
    :param y:
    :param scheme:
    :return:
    """

    gm = GlobalMercator(tileSize=512)
    if scheme != "tms":
        y = change_scheme(zoom, y)
    return gm.TileBounds(x, y, zoom)


def get_tile_bounds(
        zoom: int, extent: Tuple[float, float, float, float], source_crs: str, scheme: str = "xyz"
) -> Bounds:
    """
     * Returns the tile boundaries in XYZ scheme in the form
     [(x_min, y_min), (x_max, y_max)] where both values are tuples
    :param scheme: 
    :param zoom: 
    :param extent: 
    :param source_crs:
    :return:
    """
    if scheme not in ["xyz", "tms"]:
        raise RuntimeError("Scheme not supported: {}".format(scheme))
    tile_bounds = None
    if extent:
        lng_min = extent[0]
        lat_min = extent[1]
        lng_max = extent[2]
        lat_max = extent[3]

        xy_min = latlon_to_tile(zoom=zoom, lat=lat_min, lng=lng_min, source_crs=source_crs, scheme=scheme)
        xy_max = latlon_to_tile(zoom=zoom, lat=lat_max, lng=lng_max, source_crs=source_crs, scheme=scheme)

        x_min = min(xy_min[0], xy_max[0])
        x_max = max(xy_min[0], xy_max[0])
        y_min = min(xy_min[1], xy_max[1])
        y_max = max(xy_min[1], xy_max[1])

        max_tile = 2 ** zoom - 1
        x_max = clamp(x_max, high=max_tile)
        y_max = clamp(y_max, high=max_tile)

        tile_bounds = create_bounds(zoom, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, scheme=scheme)
    return tile_bounds


def get_all_tiles(bounds: Bounds, is_cancel_requested_handler: Callable) -> List[Tuple[int, int]]:
    tiles = []
    width = ceil(bounds.width())
    height = ceil(bounds.height())
    x_min = bounds.x_min()
    y_min = bounds.y_min()
    info("Preprocessing {} tiles", width * height)
    for x in range(width):
        if is_cancel_requested_handler():
            break
        for y in range(height):
            col = x + x_min
            row = y + y_min
            tiles.append((col, row))
    return tiles


def change_scheme(zoom: int, y: int) -> int:
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

_directions = {_UP: (0, -1), _RIGHT: (1, 0), _DOWN: (0, 1), _LEFT: (-1, 0)}


def get_tiles_from_center(
        nr_of_tiles: int, available_tiles: List[Tuple[int, int]], should_cancel_func: Callable[[], bool] = None
) -> list:
    if nr_of_tiles > len(available_tiles):
        nr_of_tiles = len(available_tiles)

    debug("Getting {} center-tiles from a total of {} tiles", nr_of_tiles, len(available_tiles))
    if nr_of_tiles is None or nr_of_tiles >= len(available_tiles) or len(available_tiles) == 0:
        return available_tiles

    min_x: int = min([t[0] for t in available_tiles])
    min_y: int = min([t[1] for t in available_tiles])
    max_x: int = max([t[0] for t in available_tiles])
    max_y: int = max([t[1] for t in available_tiles])

    center_tile_offset = (int(floor((max_x - min_x) / 2)), int(floor((max_y - min_y) // 2)))
    selected_tiles = set()
    center_tile = _sum_tiles((min_x, min_y), center_tile_offset)
    if len(selected_tiles) < nr_of_tiles and center_tile in available_tiles:
        selected_tiles.add(center_tile)

    current_tile = center_tile
    nr_of_steps = 0
    current_direction = 0
    while len(selected_tiles) < nr_of_tiles and not (should_cancel_func and should_cancel_func()):
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
    return list(selected_tiles)


def _sum_tiles(first_tile: Tuple[int, int], second_tile: Tuple[int, int]) -> Tuple[int, int]:
    return first_tile[0] + second_tile[0], first_tile[1] + second_tile[1]


def get_zoom_by_scale(scale: int) -> int:
    if scale < 0:
        return 23
    zoom = 0
    for upper_bound in sorted(_zoom_level_by_upper_scale_bound):
        if scale < upper_bound:
            zoom = _zoom_level_by_upper_scale_bound[upper_bound]
            break
    return zoom


_zoom_level_by_upper_scale_bound = {
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
    0: 23,
}
