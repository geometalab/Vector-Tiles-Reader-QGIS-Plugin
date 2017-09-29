from tile_helper import *
import pytest

def test_latlon_to_tile():
    bounds = [-180, -90, 180, 90]
    tile = latlon_to_tile(14, bounds[1], bounds[0])
    print "tile 1: ", tile
