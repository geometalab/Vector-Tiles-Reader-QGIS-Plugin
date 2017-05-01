import pytest
from tile_helper import get_tile_bounds, convert_coordinate, coordinate_to_tile, get_code_from_epsg


def test_getepsgcode():
    assert 3857 == get_code_from_epsg("EPSG:3857")
    assert 4326 == get_code_from_epsg("epsg:4326")


def test_convertcoordinate():
    r = convert_coordinate("EPSG:4326", "EPSG:3857", 46.9465123, 7.4459838)
    r = map(lambda x: int(x), r)
    assert r == [828883, 5933347, 0]


def test_convertcoordinate_topleft():
    r = coordinate_to_tile(14, lat=85.05, lng=-179.98, source_crs="epsg:4326", scheme="xyz")
    assert r == (0, 0)


def test_convertcoordinate_bottomright():
    r = coordinate_to_tile(14, lat=-85.05, lng=179.98, source_crs="epsg:4326", scheme="xyz")
    assert r == (16383, 16383)


# def test_convertcoordinate_second():
#     r = coordinate_to_tile(14, lat=85.05, lng=-180, source_crs="epsg:4326", scheme="xyz")
#     print "r: ", r
#     assert r == [0, 0]

# def test_gettilebounds():
#     b = get_tile_bounds(14, [-180, -85.0511, 180, 85.0511], "EPSG:3857", "xyz")
#     print b
#     assert b == 2
