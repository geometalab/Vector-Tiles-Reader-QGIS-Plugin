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
    "type": ConnectionTypes.MBTiles,
    "style": None
}

DIRECTORY_CONNECTION_TEMPLATE = {
    "name": None,
    "path": None,
    "type": ConnectionTypes.Directory,
    "style": None
}

TILEJSON_CONNECTION_TEMPLATE = {
    "name": "",
    "url": "",
    "token": None,
    "type": ConnectionTypes.TileJSON,
    "can_edit": None,
    "disabled": None,
    "style": ""
}

POSTGIS_CONNECTION_TEMPLATE = {
    "name": None,
    "host": None,
    "port": 5432,
    "username": "postgres",
    "password": None,
    "database": None,
    "save_password": True,
    "type": ConnectionTypes.PostGIS,
    "style": None
}