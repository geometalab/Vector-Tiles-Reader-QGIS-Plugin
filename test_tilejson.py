from tile_json import TileJSON
import pytest
from tile_helper import get_tile_bounds, coordinate_to_tile

def test_load():
    tj = _get_loaded()
    assert tj.json

def test_bounds():
    tj = _get_loaded()
    b = tj.bounds_longlat()
    assert b
    assert len(b) == 4

def test_manual_bounds():
    # boundary for mbtiles zurich 4 tiles in bottom left corner
    b = [8.268328, 47.222658, 8.298712, 47.243988]
    t = get_tile_bounds(14, b)
    assert t[0] == (8568, 5746)
    assert t[1] == (8569, 5747)

def test_tile_bounds():
    b = coordinate_to_tile(14, 47.22541, 8.27173)  # hitzkirch coordinates
    assert b
    assert b[0] == 8568
    assert b[1] == 5747

def test_tile_bounds_world():
    tj = _get_loaded()
    b = tj.bounds_tile(14)
    b_min = b[0]
    b_max = b[1]
    assert b
    assert b_min == (-1, -1)
    assert b_max == (16383, 16383)

def _get_loaded():
    tj = TileJSON("")
    tj.load()
    return tj