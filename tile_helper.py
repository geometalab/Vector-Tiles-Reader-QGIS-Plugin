from global_map_tiles import GlobalMercator
from osgeo import osr
import math


class VectorTile:
    
    decoded_data = None

    def __init__(self, scheme, zoom_level, x, y):
        self.scheme = scheme
        self.zoom_level = int(zoom_level)
        self.column = int(x)
        self.row = int(y)
    
    def __str__(self):
        return "Tile (zoom={}, col={}, row={}".format(self.zoom_level, self.column, self.row)

    def id(self):
        return "{};{}".format(self.column, self.row)


def coordinate_to_tile(zoom, lat, lng, source_crs, scheme="xyz"):
    """
     * Returns the tile-xy from the specified WGS84 lat/long coordinates
    :param zoom: 
    :param lat: 
    :param lng: 
    :param source_crs: 
    :return: 
    """
    if zoom is None:
        raise RuntimeError("zoom is required")
    if lat is None:
        raise RuntimeError("latitude is required")
    if lng is None:
        raise RuntimeError("Longitude is required")

    m = convert_coordinate(source_crs, 3857, lat, lng)
    gm = GlobalMercator()
    tile = gm.MetersToTile(m[0], m[1], zoom)
    if scheme != "tms":
        y = change_scheme(zoom, tile[1])
        tile = (tile[0], y)
    return tile


def convert_coordinate(source_crs, target_crs, lat, lng):
    source_crs = get_code_from_epsg(source_crs)
    target_crs = get_code_from_epsg(target_crs)

    src = osr.SpatialReference()
    tgt = osr.SpatialReference()
    # src.SetFromUserInput(source_crs)
    # tgt.SetFromUserInput(target_crs)
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
    gm = GlobalMercator()
    wgs84 = gm.MetersToLatLon(x, y)
    # change latlon to lonlat
    return [wgs84[1], wgs84[0]]


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


def get_tile_bounds(zoom, bounds, crs, scheme="xyz"):
    """
     * Returns the tile boundaries in XYZ scheme in the form [(x_min, y_min), (x_max, y_max)] where both values are tuples
    :param scheme: 
    :param zoom: 
    :param bounds: 
    :return: 
    """
    if scheme not in ["xyz", "tms"]:
        raise RuntimeError("Scheme not supported: {}".format(scheme))

    tiles = None
    if bounds:
        lng_min = bounds[0]
        lat_min = bounds[1]
        lng_max = bounds[2]
        lat_max = bounds[3]

        xy_min = coordinate_to_tile(zoom, lat_max, lng_min, crs, scheme)
        xy_max = coordinate_to_tile(zoom, lat_min, lng_max, crs, scheme)

        tiles = [xy_min, xy_max]
    return tiles


def change_zoom(source_zoom, target_zoom, tile, scheme, crs):
    """
    * Converts tile coordinates from one zoom-level to another
    :param source_zoom: 
    :param target_zoom: 
    :param tile: 
    :param scheme: 
    :param crs: 
    :return: 
    """
    lat_lon = tile_to_latlon(source_zoom, tile[0], tile[1], scheme)
    new_tile = coordinate_to_tile(target_zoom, lat_lon[1], lat_lon[0], crs, scheme)
    return new_tile


def get_all_tiles(bounds):
    nr_tiles_x = int(math.fabs(bounds[1][0] - bounds[0][0]) + 1)
    nr_tiles_y = int(math.fabs(bounds[1][1] - bounds[0][1]) + 1)
    tiles = []
    for x in range(nr_tiles_x):
        for y in range(nr_tiles_y):
            col = x + bounds[0][0]
            row = y + bounds[0][1]
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
