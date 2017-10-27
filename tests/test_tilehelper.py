from tile_helper import *
import pytest

def test_latlon_to_tile():
    bounds = [-180, -90, 180, 90]
    tile = latlon_to_tile(14, bounds[1], bounds[0])
    print "tile 1: ", tile

def test_get_zoom_by_scale_min():
    zoom = get_zoom_by_scale(-1)
    assert zoom == 23


def test_get_zoom_by_scale_max():
    zoom = get_zoom_by_scale(10000000000)
    assert zoom == 0
