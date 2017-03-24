import pytest
from file_helper import FileHelper


def test_is_not_sqlite_db():
    file = "./sample data/invalid.mbtiles"
    assert not FileHelper.is_sqlite_db(file)


def test_is_sqlite_db():
    file = "./sample data/winterthur_switzerland.mbtiles"
    assert FileHelper.is_sqlite_db(file)


def test_is_mapbox_pbf():
    file = "./sample data/zh.pbf"
    with open(file, 'r') as f:
        content = f.read(10)
    assert FileHelper.is_mapbox_pbf(content)


def test_is_not_mapbox_pbf():
    file = "./sample data/png.pbf"
    with open(file, 'r') as f:
        content = f.read(10)
    assert not FileHelper.is_mapbox_pbf(content)
