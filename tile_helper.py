from global_map_tiles import GlobalMercator
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


def coordinate_to_tile(zoom, lat, lng):
    gm = GlobalMercator()
    m = gm.LatLonToMeters(lat, lng)
    t = gm.MetersToTile(m[0], m[1], zoom)
    tile = gm.GoogleTile(t[0], t[1], zoom)
    return tile


def epsg3857_to_wgs84_lonlat(x, y):
    gm = GlobalMercator()
    wgs84 = gm.MetersToLatLon(x, y)
    # change latlon to lonlat
    return [wgs84[1], wgs84[0]]


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

    tiles = None
    if bounds:
        lng_min = bounds[0]
        lat_min = bounds[1]
        lng_max = bounds[2]
        lat_max = bounds[3]

        xy_min = coordinate_to_tile(zoom, lat_max, lng_min)
        xy_max = coordinate_to_tile(zoom, lat_min, lng_max)

        is_tms_scheme = scheme == "tms"
        if is_tms_scheme:
            xy_min = (xy_min[0], change_scheme(zoom, xy_min[1]))
            xy_max = (xy_max[0], change_scheme(zoom, xy_max[1]))

        tiles = [xy_min, xy_max]
    return tiles


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
