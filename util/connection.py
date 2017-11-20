class _ConnectionTypes(object):
    def __init__(self):
        pass

    TileJSON = "TileJSON"
    MBTiles = "MBTiles"
    Directory = "Directory"
    PostGIS = "PostGIS"


ConnectionTypes = _ConnectionTypes()

MBTILES_CONNECTION_TEMPLATE = {
    "name": None,
    "path": None,
    "type": ConnectionTypes.MBTiles
}

DIRECTORY_CONNECTION_TEMPLATE = {
    "name": None,
    "path": None,
    "type": ConnectionTypes.Directory
}

TILEJSON_CONNECTION_TEMPLATE = {
    "name": None,
    "url": None,
    "token": None,
    "type": ConnectionTypes.TileJSON,
    "can_edit": None
}

POSTGIS_CONNECTION_TEMPLATE = {
    "name": None,
    "host": None,
    "port": 5432,
    "username": "postgres",
    "password": None,
    "database": None,
    "save_password": True,
    "type": ConnectionTypes.PostGIS
}