from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import object
from file_helper import *
import os
import sys
import json
import sqlite3
import uuid
import mapbox_vector_tile

from io import StringIO
from gzip import GzipFile
from log_helper import critical, info, debug
from global_map_tiles import GlobalMercator
from tile_helper import change_scheme
from feature_helper import geo_types, is_multi
from PyQt4.QtGui import QMessageBox, QApplication


class VtWriter(object):

    def __init__(self, iface, file_destination, progress_handler):
        self.iface = iface
        self.file_destination = file_destination
        self.progress_handler = progress_handler
        self.metadata = {
            "exporter": "QGIS Vector Tiles Reader Plugin",
            "scheme": "tms",
            "json": None,
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
        self._cancel_requested = False
        self.layer_names = set()

    def _update_progress(self, title=None, show_dialog=None, progress=None, max_progress=None, msg=None):
        if self.progress_handler:
            self.progress_handler(title, progress, max_progress, msg, show_dialog)

    def _get_metadata(self, field):
        return self.metadata[field]

    def _set_metadata(self, field, value):
        self.metadata[field] = value

    def _get_layers(self):
        all_layers = self.iface.legendInterface().selectedLayers(True)
        if len(all_layers) == 0:
            all_layers = self.iface.legendInterface().layers()
        return all_layers

    def cancel(self):
        self._cancel_requested = True

    def export(self):
        self._cancel_requested = False
        self.conn = None
        try:
            self.conn = self._create_db()
        except:
            critical("db creation failed: {}", sys.exc_info())

        if self.conn:
            try:
                with self.conn:
                    tile_names = self._get_loaded_tile_names()
                    if tile_names:
                        tiles = self._load_tiles(tile_names)
                        nr_tiles = len(tiles)
                        for index, t in enumerate(tiles):
                            if self._cancel_requested:
                                break

                            self._update_progress(title="Export tile {}/{}".format(index+1, nr_tiles), show_dialog=True)
                            QApplication.processEvents()
                            self._update_bounds(t)
                            debug("layers to export: {}", self.layers_to_export)
                            self._save_tile(t)

                        if not self._cancel_requested:
                            layer_objects = [{"id": l} for l in self.layer_names]
                            vector_layers = {"vector_layers": layer_objects}
                            self.metadata["json"] = json.dumps(vector_layers)
                            self._save_metadata()
                            debug("export complete")
                            self.iface.messageBar().pushInfo(u'Vector Tiles Reader', u'mbtiles export completed')
                        else:
                            debug("export cancelled")
                            self.iface.messageBar().pushInfo(u'Vector Tiles Reader', u'mbtiles export cancelled')
                self.conn.close()
            except:
                if self.conn:
                    self.conn.close()
                critical("Export failed: {}", sys.exc_info())
                raise
        self._update_progress(show_dialog=False)

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
        all_layers = self._get_layers()

        self.layers_to_export = [l.shortName() for l in all_layers]

        source_to_export = None
        warning_shown = False

        temp_dir = os.path.normpath(get_temp_dir()).lower()
        tile_names = set()
        for l in all_layers:
            layer_source = l.source()
            if os.path.normpath(layer_source).lower().startswith(temp_dir):
                with open(layer_source, "r") as f:
                    feature_collection = json.load(f)
                    source_name = feature_collection["source"]

                    if source_to_export is None:
                        source_to_export = source_name
                    elif source_to_export != source_name:
                        if not warning_shown:
                            warning_shown = True
                            msg = "You're trying to export tiles of multiple sources. Only the source '{}' will be exported." \
                                  " Do you want to continue?".format(source_to_export)
                            result = QMessageBox.warning(None, "Multiple Sources", msg,
                                                         QMessageBox.Ok | QMessageBox.Cancel)
                            if result == QMessageBox.Cancel:
                                return None
                        continue

                    source_scheme = feature_collection["scheme"]
                    zoom_level = int(feature_collection["zoom_level"])

                    min_zoom = self._get_metadata("minzoom")
                    max_zoom = self._get_metadata("maxzoom")
                    source_id = self._get_metadata("id")

                    if not self.source_scheme:
                        self.source_scheme = source_scheme
                    if not source_id:
                        self._set_metadata("id", source_name)
                    if not min_zoom or zoom_level < min_zoom:
                        self._set_metadata("minzoom", zoom_level)
                    if not max_zoom or zoom_level > max_zoom:
                        self._set_metadata("maxzoom", zoom_level)

                    collection_tiles = [(int(t.split(";")[0]), int(t.split(";")[1])) for t in feature_collection["tiles"]]
                    for t in collection_tiles:
                        cached_tile_name = get_cached_tile_file_name(source_name, zoom_level, t[0], t[1])
                        tile_names.add(cached_tile_name)
        return tile_names

    def _load_tiles(self, tile_names):
        tiles = []
        for name in tile_names:
            tile = get_cached_tile(name)
            if tile:
                if self.source_scheme != "tms":
                    tile.row = change_scheme(tile.zoom_level, tile.row)
                tiles.append(tile)
        return tiles

    def _save_metadata(self):
        self.metadata["bounds"] = "{},{},{},{}".format(self.min_lon, self.min_lat, self.max_lon, self.max_lat)
        for k in self.metadata:
            insert_sql = "INSERT INTO metadata(name, value) VALUES(?,?)"
            self.conn.execute(insert_sql, (k, self.metadata[k]))

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

        self._update_progress(max_progress=len(tile.decoded_data))

        all_layers = []
        for index, layer_name in enumerate(tile.decoded_data):
            if self._cancel_requested:
                return

            self._update_progress(msg="Export '{}' of zoom level {}".format(layer_name, tile.zoom_level))
            if layer_name in self.layers_to_export:
                converted_layer = self._convert_layer(layer_name, tile)
                all_layers.append(converted_layer)
            self._update_progress(progress=index+1)

        encoded_data = mapbox_vector_tile.encode(all_layers)
        if self._cancel_requested:
            return

        out = StringIO()
        with GzipFile(fileobj=out, mode="w") as f:
            f.write(encoded_data)
        gzipped_data = out.getvalue()

        insert_sql = "INSERT INTO images(tile_id, tile_data) VALUES(?,?)"
        self.conn.execute(insert_sql, (tile_id, sqlite3.Binary(gzipped_data)))

    def _convert_layer(self, layer_name, tile):
        layer = tile.decoded_data[layer_name]
        self.layer_names.add(layer_name)
        converted_layer = {
            "name": layer_name,
            "features": []}
        debug("current layer: {}", layer_name)
        for k in list(layer.keys()):
            if k != "features":
                converted_layer[k] = layer[k]

        for f in layer["features"]:
            geo_type = geo_types[f["type"]]
            geom_string = geo_type.upper()
            geometry = f["geometry"]

            is_polygon = geom_string == "POLYGON"
            is_multi_geometry = is_multi(geo_type, geometry)
            all_geometries = []
            if is_multi_geometry:
                VtWriter.get_subarr(geometry, all_geometries)
            else:
                if all(VtWriter.is_coordinate_tuple(c) for c in geometry):
                    all_geometries = [geometry]
                else:
                    all_geometries = geometry

            for geom in all_geometries:
                new_feature = self._copy_feature(f)
                new_feature["geometry"] = self._create_wkt_geometry(geo_type, is_polygon, geom)
                try:
                    single_feature_layer = {"name": "dummy", "features": [new_feature]}
                    mapbox_vector_tile.encode(single_feature_layer, y_coord_down=True)
                    converted_layer["features"].append(new_feature)
                except:
                    debug("invalid geometry: {}", new_feature["geometry"])
                    pass
        return converted_layer

    @staticmethod
    def get_subarr(arr, result):
        if all(VtWriter.is_coordinate_tuple(c) for c in arr):
            result.append(arr)
        else:
            for subarr in arr:
                VtWriter.get_subarr(subarr, result)

    @staticmethod
    def is_coordinate_tuple(coordinates):
        return len(coordinates) == 2 and all(isinstance(c, int) for c in coordinates)

    @staticmethod
    def _copy_feature(f):
        """
         * Creates a clone of the feature but excludes the geometry
        :param f:
        :return:
        """

        new_feature = {}
        for k in list(f.keys()):
            if k != "geometry":
                new_feature[k] = f[k]
        return new_feature

    @staticmethod
    def _create_wkt_geometry(geo_type, is_polygon, geom):
        geo_type_string = geo_type.upper()
        if is_polygon:
            geo_type_string += "(({}))"
        else:
            geo_type_string += "({})"

        coords_string = ""

        for index, c in enumerate(geom):
            coords_string += "{} {}".format(c[0], c[1])
            if index < len(geom)-1:
                coords_string += ", "
        geom_string = geo_type_string.format(coords_string)
        return geom_string

