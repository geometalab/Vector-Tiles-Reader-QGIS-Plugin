from file_helper import FileHelper
import os
import sys
import json
import sqlite3
import uuid
import mapbox_vector_tile

from cStringIO import StringIO
from gzip import GzipFile
from log_helper import critical
from vt_reader import GeoTypes, VtReader
from global_map_tiles import GlobalMercator

class VtWriter:

    geo_types = {
        1: GeoTypes.POINT,
        2: GeoTypes.LINE_STRING,
        3: GeoTypes.POLYGON}

    def __init__(self, iface, file_destination):
        self.iface = iface
        self.file_destination = file_destination
        self.metadata = {
            "scheme": "tms",
            "json": {"vector_layers": []},
            "id": None,
            "minzoom": None,
            "maxzoom": None}
        self.min_zoom = None
        self.max_zoom = None
        self.min_lon = None
        self.max_lon = None
        self.min_lat = None
        self.max_lat = None

    def _get_metadata(self, field):
        return self.metadata[field]

    def _set_metadata(self, field, value):
        self.metadata[field] = value

    def export(self):
        self.conn = None
        try:
            self.conn = self._create_db()
        except:
            critical("db creation failed: {}", sys.exc_info())

        if self.conn:
            try:
                with self.conn:
                    tile_names = self._get_loaded_tile_names()
                    tiles = self._load_tiles(tile_names)
                    for t in tiles:
                        self._update_bounds(t)
                        self._save_tile(t)
                        break
                    self._save_metadata()
                # self.conn.close()
            except:
                if self.conn:
                    self.conn.close()
                raise
                # critical("Export failed: {}", sys.exc_info())

    def _save_metadata(self):
        self.metadata["bounds"] = "{},{},{},{}".format(self.min_lon, self.min_lat, self.max_lon, self.max_lat)
        for k in self.metadata:
            print "metadata: ", k, self.metadata[k]
            insert_sql = "INSERT INTO metadata(name, value) VALUES(?,?)"
            self.conn.execute(insert_sql, (k, str(self.metadata[k]).replace("'", "\"").replace("\": u\"", "\": \"")))

    def _update_bounds(self, tile):
        gm = GlobalMercator()
        latlon = gm.TileLatLonBounds(tile.column, tile.row, tile.zoom_level)

        self.min_lat = self._get_min(self.min_lat, latlon[0])
        self.min_lon = self._get_min(self.min_lon, latlon[1])
        self.max_lat = self._get_max(self.max_lat, latlon[2])
        self.max_lon = self._get_max(self.max_lon, latlon[3])

    def _get_min(self, current_value, new_value):
        if not current_value or new_value < current_value:
            return new_value
        else:
            return current_value

    def _get_max(self, current_value, new_value):
        if not current_value or new_value > current_value:
            return new_value
        else:
            return current_value

    def _save_tile(self, tile):
        id = str(uuid.uuid4())
        insert_tile = "INSERT INTO map(tile_id, zoom_level, tile_column, tile_row) VALUES(?,?,?,?)"
        self.conn.execute(insert_tile, (id, tile.zoom_level, tile.column, tile.row))

        layer_name = tile.decoded_data.keys()[0]
        layer = tile.decoded_data[layer_name]

        self._get_metadata("json")["vector_layers"].append({"id": layer_name})

        converted_layer = {
            "name": layer_name,
            "features": []}
        for k in layer.keys():
            if k != "features":
                converted_layer[k] = layer[k]

        # print "nr  features: ", len(layer["features"])

        for f in layer["features"]:
            for geom in f["geometry"]:
                new_feature = {}
                for k in f.keys():
                    if k != "geometry":
                        new_feature[k] = f[k]
                new_feature["geometry"] = self._convert_geometry(f["type"], geom)
                try:
                    single_feature_layer = {"name": "dummy", "features": [new_feature]}
                    encoded_single_feature = mapbox_vector_tile.encode(single_feature_layer)
                    converted_layer["features"].append(new_feature)
                except:
                    print "encoding failed: ", new_feature, sys.exc_info()
                    print "original feature: ", f
                # break

        encoded_data = mapbox_vector_tile.encode(converted_layer)
        out = StringIO()
        with GzipFile(fileobj=out, mode="w") as f:
            f.write(encoded_data)
        gzipped_data = out.getvalue()
        print "gzip done"

        insert_sql = "INSERT INTO images(tile_id, tile_data) VALUES(?,?)"
        self.conn.execute(insert_sql, (id, sqlite3.Binary(gzipped_data)))

    def _convert_geometry(self, geo_type, geom):
        geom_string = self.geo_types[geo_type].upper()
        if geom_string == "POLYGON":
            geom_string += "(({}))"
        else:
            geom_string += "({})"

        coords_string = ""
        coords = []
        VtReader._map_coordinates_recursive(geom, func=lambda c: coords.append(c))
        for index, c in enumerate(coords):
            coords_string += "{} {}".format(c[0], c[1])
            if index < len(coords)-1:
                coords_string += ", "
        geom_string = geom_string.format(coords_string)
        return geom_string



    def _create_db(self):
        if os.path.isfile(self.file_destination):
            os.remove(self.file_destination)

        conn = sqlite3.connect(self.file_destination)
        conn.execute("CREATE TABLE metadata ( name text, value text )")
        conn.execute("CREATE TABLE map ( zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_id TEXT, grid_id TEXT )")
        conn.execute("CREATE TABLE images ( tile_data blob, tile_id text )")
        conn.execute("CREATE UNIQUE INDEX images_id ON images (tile_id)")
        conn.execute("CREATE INDEX map_grid_id ON map (grid_id)")
        conn.execute("CREATE UNIQUE INDEX map_index ON map (zoom_level, tile_column, tile_row)")
        conn.execute("CREATE UNIQUE INDEX name ON metadata (name)")
        conn.execute("""
                            CREATE VIEW tiles AS
                            SELECT map.zoom_level AS zoom_level,
                                  map.tile_column AS tile_column,
                                  map.tile_row AS tile_row,
                                  images.tile_data AS tile_data
                            FROM map
                              JOIN images
                                ON images.tile_id = map.tile_id""")
        return conn

    def _get_loaded_tile_names(self):
        all_layers = self.iface.legendInterface().layers()
        tile_names = set()
        for l in all_layers:
            layer_source = l.source()
            if layer_source.startswith(FileHelper.get_temp_dir()):
                with open(layer_source, "r") as f:
                    feature_collection = json.load(f)
                    source_name = feature_collection["source"]
                    zoom_level = int(feature_collection["zoom_level"])

                    min_zoom = self._get_metadata("minzoom")
                    max_zoom = self._get_metadata("maxzoom")
                    source_id = self._get_metadata("id")

                    if not source_id:
                        self._set_metadata("id", source_name)
                    if not min_zoom or zoom_level < min_zoom:
                        self._set_metadata("minzoom", zoom_level)
                    if not max_zoom or zoom_level > max_zoom:
                        self._set_metadata("maxzoom", zoom_level)

                    collection_tiles = map(lambda t: (int(t.split(";")[0]), int(t.split(";")[1])), feature_collection["tiles"])
                    for t in collection_tiles:
                        cached_tile_name = FileHelper.get_cached_tile_file_name(source_name, zoom_level, t[0], t[1])
                        tile_names.add(cached_tile_name)
        return tile_names

    def _load_tiles(self, tile_names):
        tiles = []
        for name in tile_names:
            tile = FileHelper.get_cached_tile(name)
            if tile:
                tiles.append(tile)
        return tiles
