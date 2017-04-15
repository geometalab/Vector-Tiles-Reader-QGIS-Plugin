from global_map_tiles import GlobalMercator


class VectorTile:
    
    decoded_data = None

    def __init__(self, zoom_level, x, y):
        self.zoom_level = zoom_level
        self.column = x
        self.row = y
    
    def __str__(self):
        return "Tile (zoom={}, col={}, row={}".format(self.zoom_level, self.column, self.row)


def coordinate_to_tile(zoom, lat, lng):
    gm = GlobalMercator()
    m = gm.LatLonToMeters(lat, lng)
    t = gm.MetersToTile(m[0], m[1], zoom)
    tile = gm.GoogleTile(t[0], t[1], zoom)
    return tile


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
            xy_min = (xy_min[0], _change_scheme(zoom, xy_min[1]))
            xy_max = (xy_max[0], _change_scheme(zoom, xy_max[1]))

        tiles = [xy_min, xy_max]
    return tiles


def _change_scheme(zoom, y):
    return (2 ** zoom) - y - 1
