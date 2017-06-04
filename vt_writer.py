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
from global_map_tiles import GlobalMercator
from tile_helper import change_scheme
from feature_helper import GeoTypes, geo_types, is_multi, map_coordinates_recursive


class VtWriter:

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
        self.layers_to_export = None
        self.source_scheme = None

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
                        print "layers to export: ", self.layers_to_export
                        self._save_tile(t)
                    self._save_metadata()
            except:
                if self.conn:
                    self.conn.close()
                raise
                # critical("Export failed: {}", sys.exc_info())
        print "export complete"

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
        tile_id = str(uuid.uuid4())
        insert_tile = "INSERT INTO map(tile_id, zoom_level, tile_column, tile_row) VALUES(?,?,?,?)"
        self.conn.execute(insert_tile, (tile_id, tile.zoom_level, tile.column, tile.row))

        all_layers = []
        for layer_name in tile.decoded_data:
            if layer_name in self.layers_to_export:
                converted_layer = self.convert_layer(layer_name, tile)
                all_layers.append(converted_layer)

        encoded_data = mapbox_vector_tile.encode(all_layers)
        out = StringIO()
        with GzipFile(fileobj=out, mode="w") as f:
            f.write(encoded_data)
        gzipped_data = out.getvalue()
        print "gzip done"

        insert_sql = "INSERT INTO images(tile_id, tile_data) VALUES(?,?)"
        self.conn.execute(insert_sql, (tile_id, sqlite3.Binary(gzipped_data)))

    def convert_layer(self, layer_name, tile):
        layer = tile.decoded_data[layer_name]
        self._get_metadata("json")["vector_layers"].append({"id": layer_name})
        converted_layer = {
            "name": layer_name,
            "features": []}
        print "current layer: ", layer_name
        for k in layer.keys():
            if k != "features":
                converted_layer[k] = layer[k]

        for f in layer["features"]:
            geo_type = geo_types[f["type"]]
            geom_string = geo_type.upper()
            geometry = f["geometry"]
            if geo_type == GeoTypes.POINT:
                geometry = geometry[0]

            is_polygon = geom_string == "POLYGON"
            is_multi_geometry = is_multi(geo_type, geometry)
            all_geometries = []
            if not is_multi_geometry:
                all_geometries = [geometry]
            else:
                all_geometries.extend(geometry)

            for geom in all_geometries:
                new_feature = self.create_feature(f, geom, geo_type, is_polygon)
                try:
                    single_feature_layer = {"name": "dummy", "features": [new_feature]}
                    mapbox_vector_tile.encode(single_feature_layer, y_coord_down=True)
                    converted_layer["features"].append(new_feature)
                except:
                    # todo: handle invalid geometries
                    pass
        return converted_layer

    def create_feature(self, f, geom, geo_type, is_polygon):
        new_feature = {}
        for k in f.keys():
            if k != "geometry":
                new_feature[k] = f[k]
        new_feature["geometry"] = self._convert_geometry(geo_type, is_polygon, geom)
        return new_feature

    def _convert_geometry(self, geo_type, is_polygon, geom):
        geo_type_string = geo_type.upper()
        if is_polygon:
            geo_type_string += "(({}))"
        else:
            geo_type_string += "({})"

        coords_string = ""
        coords = []

        if geo_type == GeoTypes.POINT:
            coords = [geom]
        else:
            map_coordinates_recursive(geom, mapper_func=lambda c: coords.append(c))

        for index, c in enumerate(coords):
            coords_string += "{} {}".format(c[0], c[1])
            if index < len(coords)-1:
                coords_string += ", "
        geom_string = geo_type_string.format(coords_string)
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
        all_layers = self.iface.legendInterface().selectedLayers(True)
        if len(all_layers) == 0:
            all_layers = self.iface.legendInterface().layers()

        self.layers_to_export = map(lambda l: l.shortName(), all_layers)

        tile_names = set()
        for l in all_layers:
            layer_source = l.source()
            if layer_source.startswith(FileHelper.get_temp_dir()):
                with open(layer_source, "r") as f:
                    feature_collection = json.load(f)
                    source_name = feature_collection["source"]
                    source_scheme = feature_collection["scheme"]
                    zoom_level = int(feature_collection["zoom_level"])

                    min_zoom = self._get_metadata("minzoom")
                    max_zoom = self._get_metadata("maxzoom")
                    source_id = self._get_metadata("id")
                    scheme = self._get_metadata("scheme")

                    if not scheme:
                        self.source_scheme = source_scheme
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
                if self.source_scheme != "tms":
                    tile.row = change_scheme(tile.zoom_level, tile.row)
                tiles.append(tile)
        return tiles
