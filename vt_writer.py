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

class VtWriter:

    geo_types = {
        1: GeoTypes.POINT,
        2: GeoTypes.LINE_STRING,
        3: GeoTypes.POLYGON}

    def __init__(self, iface, file_destination):
        self.iface = iface
        self.file_destination = file_destination

    def export(self):
        self.conn = None
        try:
            self.conn = self._create_db()
        except:
            critical("db creation failed: {}", sys.exc_info())

        if self.conn:
            try:
                tile_names = self._get_loaded_tile_names()
                tiles = self._load_tiles(tile_names)
                for t in tiles:
                    self._save_tile(t)
                    break
                self.conn.close()
            except:
                if self.conn:
                    self.conn.close()
                raise
                # critical("Export failed: {}", sys.exc_info())

    def _save_tile(self, tile):
        id = str(uuid.uuid4())
        insert_tile = "INSERT INTO map(tile_id, zoom_level, tile_column, tile_row) VALUES(?,?,?,?)"
        insert_data = "INSERT INTO images(tile_id, tile_data) VALUES(?,?)"

        # self.conn.execute(insert_tile, (id, tile.zoom_level, tile.column, tile.row))
        data = tile.decoded_data.itervalues().next()
        layer_name = tile.decoded_data.keys()[0]
        layer = tile.decoded_data[layer_name]
        # layer["name"] = layer_name

        converted_layer = {
            "name": layer_name,
            "features": []}
        for k in layer.keys():
            if k != "features":
                converted_layer[k] = layer[k]

        print "nr  features: ", len(layer["features"])

        for f in layer["features"]:
            print "feature: ", f
            new_feature = {}
            for k in f.keys():
                if k != "geometry":
                    new_feature[k] = f[k]
            new_feature["geometry"] = self._convert_geometry(f["type"], f["geometry"])
            converted_layer["features"].append(new_feature)
            break

        print "converted layer: ", converted_layer

        # layer = {
        #         'version': 2,
        #         'features': [{
        #                 'geometry': "POLYGON ((4160 -64, -64 -64, -64 4160, 4160 4160, 4160 -64))",
        #                 'type': 3,
        #                 'properties': {
        #                     'class': 'ocean'
        #                 },
        #                 'id': 1L
        #             }
        #         ],
        #         'extent': 4096,
        #         'name': 'water'
        #     }

        # print "decoded: ", layer

        encoded_data = mapbox_vector_tile.encode(converted_layer)
        out = StringIO()
        with GzipFile(fileobj=out, mode="w") as f:
            f.write(encoded_data)
        gzipped_data = out.getvalue()
        print "gzip done"

        # self.conn.execute(insert_data, (id, gzipped_data))

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
        # conn.execute("CREATE TABLE metadata ( name text, value text )")
        # conn.execute("CREATE TABLE map ( zoom_level INTEGER, tile_column INTEGER, tile_row INTEGER, tile_id TEXT, grid_id TEXT )")
        # conn.execute("CREATE TABLE images ( tile_data blob, tile_id text )")
        # conn.execute("CREATE UNIQUE INDEX images_id ON images (tile_id)")
        # conn.execute("CREATE INDEX map_grid_id ON map (grid_id)")
        # conn.execute("CREATE UNIQUE INDEX map_index ON map (zoom_level, tile_column, tile_row)")
        # conn.execute("CREATE UNIQUE INDEX name ON metadata (name)")
        # conn.execute("""
        #                     CREATE VIEW tiles AS
        #                     SELECT map.zoom_level AS zoom_level,
        #                           map.tile_column AS tile_column,
        #                           map.tile_row AS tile_row,
        #                           images.tile_data AS tile_data
        #                     FROM map
        #                       JOIN images
        #                         ON images.tile_id = map.tile_id""")
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
                    zoom_level = feature_collection["zoom_level"]
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
