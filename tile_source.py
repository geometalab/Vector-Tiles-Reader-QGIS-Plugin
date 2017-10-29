from future import standard_library
standard_library.install_aliases()
from builtins import str
import sqlite3
import urllib.parse
import json
import os
import sys

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.QtSql import QSqlDatabase, QSqlQuery
from tile_json import TileJSON
from log_helper import info, warn, critical, debug
from tile_helper import VectorTile, get_tiles_from_center, get_tile_bounds, tile_to_latlon, epsg3857_to_wgs84_lonlat
from network_helper import url_exists, load_url_async
from file_helper import is_sqlite_db

_DEFAULT_CRS = "EPSG:3857"


class AbstractSource(QObject):

    progress_changed = pyqtSignal(int, name='tileSourceProgressChanged')
    max_progress_changed = pyqtSignal(int, name='tileSourceMaxProgressChanged')
    message_changed = pyqtSignal('QString', name='tileSourceMessageChanged')
    tile_limit_reached = pyqtSignal(name='tile_limit_reached')

    def __init__(self):
        QObject.__init__(self)
        self._cancelling = False

    def cancel(self):
        self._cancelling = True

    def source(self):
        raise NotImplementedError

    def vector_layers(self):
        raise NotImplementedError

    def close_connection(self):
        pass

    def name(self):
        raise NotImplementedError

    def min_zoom(self):
        """
         * Returns the minimum zoom that is found in either the metadata or the tile table
        :return:
        """
        raise NotImplementedError

    def max_zoom(self):
        """
         * Returns the maximum zoom that is found in either the metadata or the tile table
        :return:
        """
        raise NotImplementedError

    def mask_level(self):
        """
         * Returns the mask level from the metadata table
        :return:
        """
        raise NotImplementedError

    def scheme(self):
        raise NotImplementedError

    def bounds_tile(self, zoom):
        """
         * Returns the tile boundaries
        :param zoom:
        :return:
        """
        raise NotImplementedError

    def crs(self):
        raise NotImplementedError

    def load_tiles(self, zoom_level, tiles_to_load, max_tiles=None):
        """
         * Loads the tiles for the specified zoom_level and bounds from the web service this source has been created with
        :param tiles_to_load: All tile coordinates which shall be loaded
        :param zoom_level: The zoom level which will be loaded
        :param max_tiles: The maximum number of tiles to be loaded
        :param limit_reacher_handler: A function which will be called, if the potential nr of tiles is greater than the specified limit
        :return:
        """
        raise NotImplementedError


class ServerSource(AbstractSource):
    def __init__(self, url):
        AbstractSource.__init__(self)
        if not url:
            raise RuntimeError("URL is required")

        valid, error = url_exists(url)
        if not valid:
            raise RuntimeError(error)

        self.url = url
        is_web_source = url.lower().startswith("http://") or url.lower().startswith("https://")
        if not is_web_source:
            raise RuntimeError("The URL is invalid: {}".format(url))

        self.json = TileJSON(url)
        self.json.load()

    def source(self):
        return self.url

    def vector_layers(self):
        return self.json.vector_layers()

    def close_connection(self):
        pass

    def name(self):
        name = self.json.name()
        if not name:
            name = self.json.id()
        if not name:
            name = urllib.parse.urlsplit(self.url)[1]
        return name

    def min_zoom(self):
        return int(self.json.min_zoom())

    def max_zoom(self):
        return int(self.json.max_zoom())

    def mask_level(self):
        return self.json.mask_level()

    def scheme(self):
        return self.json.scheme()

    def bounds_tile(self, zoom):
        return self.json.bounds_tile(zoom)

    def crs(self):
        return self.json.crs()

    def load_tiles(self, zoom_level, tiles_to_load, max_tiles=None):
        self._cancelling = False
        base_url = self.json.tiles()[0]
        urls = []
        if max_tiles and len(tiles_to_load) > max_tiles:
            tiles_to_load = get_tiles_from_center(max_tiles, tiles_to_load, should_cancel_func=lambda: self._cancelling)
            self.tile_limit_reached.emit()

        parameters = urllib.parse.parse_qs(urllib.parse.urlparse(self.url).query)
        api_key = ""
        if "api_key" in list(parameters.keys()):
            api_key = parameters["api_key"][0]
        for t in tiles_to_load:
            col = t[0]
            row = t[1]
            load_url = base_url\
                .replace("{z}", str(int(zoom_level)))\
                .replace("{x}", str(int(col)))\
                .replace("{y}", str(int(row)))\
                .replace("{api_key}", str(api_key))
            urls.append((load_url, col, row))

        self.max_progress_changed.emit(len(urls))
        self.message_changed.emit("Getting {} tiles from source...".format(len(urls)))
        return self._load_urls_async(zoom_level, urls)

    def _load_urls_async(self, zoom_level, urls_with_col_and_row):
        replies = [(load_url_async(url[0]), (url[1], url[2])) for url in urls_with_col_and_row]
        total_nr_of_requests = len(replies)
        all_finished = False
        nr_finished_before = 0
        finished_tiles = set()
        nr_finished = 0
        all_tiles = []
        while not all_finished and not self._cancelling:
            results = []
            new_finished = [r for r in replies if r[0].isFinished() and r[1] not in finished_tiles]
            nr_finished += len(new_finished)
            for r in new_finished:
                reply = r[0]
                error = reply.error()
                if error:
                    info("Error during network request: {}", error)
                else:
                    content = reply.readAll().data()
                    tile_coord = r[1]
                    finished_tiles.add(tile_coord)
                    results.append((content, tile_coord))
                reply.deleteLater()
            QApplication.processEvents()
            all_finished = nr_finished == total_nr_of_requests
            if nr_finished != nr_finished_before:
                nr_finished_before = nr_finished
                self.progress_changed.emit(nr_finished)
                tiles_with_data = [self._create_vector_tile_from_respond(zoom_level, r) for r in results]
                all_tiles.extend(tiles_with_data)
        if not all_finished and self._cancelling:
            unfinished_requests = [r for r in replies if not r[0].isFinished]
            for r in unfinished_requests:
                r.abort()
        if self._cancelling:
            all_tiles = []
        return all_tiles

    def _create_vector_tile_from_respond(self, zoom_level, r):
        content = r[0]
        col = r[1][0]
        row = r[1][1]
        tile = VectorTile(self.scheme(), zoom_level, col, row)
        return tile, content


class PostGISSource(AbstractSource):
    def __init__(self, host, port, user, password, database):
        AbstractSource.__init__(self)
        self.host = host
        self.port = port
        self._user = user
        self._password = password
        self._database = database
        self.table = None
        self.geom_column = None
        self.database = None
        self._conn = None
        self._cursor = None
        self._layers = None
        self._bounds = None
        self._db = None
        self._connect()

    def source(self):
        if self.database:
            return "pg_{}_{}".format(self.host, self.database)
        return self.host

    def _connect(self):
        db = QSqlDatabase.addDatabase("QPSQL")
        db.setHostName(self.host)
        db.setPort(int(self.port))
        db.setDatabaseName(self._database)
        db.setUserName(self._user)
        db.setPassword(self._password)
        ok = db.open()
        if not ok:
            info("Connection to database failed...")
        self._db = db
        self._layers = None

    def databases(self):
        query = """
        SELECT datname "name"
        FROM pg_database
        WHERE datistemplate = false;
        """
        databases = self._fetch_all(query)
        names = map(lambda db: db["name"], databases)
        return names

    def set_database(self, name):
        self.database = name
        self._connect()

    def _get_table_tile_query(self, geom_column, table):
        return """
            SELECT 
            ST_AsMVTGeom(
                    {},
                    ST_Makebox2d(
                        ST_transform(ST_SetSrid(ST_MakePoint(?, ?),4326),3857),
                        ST_transform(ST_SetSrid(ST_MakePoint(?, ?),4326),3857)
                        ),
                    4096, -- tile extent
                    256,  -- buffer size pixel
                    false  -- clip
                ) AS geom 
            FROM {}
        """.format(geom_column, table)

    def load_tiles(self, zoom_level, tiles_to_load, max_tiles=None):
        # geom_column = self._get_geom_column()
        # if not geom_column:
        #     raise "No geometry column found in table '{}'".format(self.table)

        if max_tiles and len(tiles_to_load) > max_tiles:
            tiles_to_load = get_tiles_from_center(max_tiles, tiles_to_load, should_cancel_func=lambda: self._cancelling)
            self.tile_limit_reached.emit()

        tile_data_tuples = []
        layer_names = map(lambda v: v["id"], self.vector_layers())
        info("layer names: {} count={}", layer_names, len(layer_names))

        queries = map(lambda l: self._get_table_tile_query(geom_column="geom", table=l), layer_names)
        joined_query = " union all ".join(queries)
        info("joined query: {}", joined_query)

        for t in tiles_to_load:
            tile_col = t[0]
            tile_row = t[1]
            latlon = tile_to_latlon(zoom_level, tile_col,tile_row, self.scheme())
            x_min, y_min = epsg3857_to_wgs84_lonlat(latlon[0], latlon[1])
            x_max, y_max = epsg3857_to_wgs84_lonlat(latlon[2], latlon[3])

            query = """
            SELECT ST_AsMVT(tile) as "mvt"
            FROM ({}) AS tile;
            """.format(joined_query)

            info("query: {}", query)
            info("query params: {}", (x_min, y_max, x_max, y_min))

            record = self._fetch_one(query, (x_min, y_min, x_max, y_max)*len(layer_names), binary_result=True)
            tile = VectorTile(self.scheme(), zoom_level, tile_col, tile_row)
            tile_data_tuples.append((tile, record["mvt"]))
        return tile_data_tuples

    def vector_layers(self):
        return [{"id": "address_p"}]

        if self._layers:
            return self._layers

        query = """
        select f_table_name as "layer_name"
        from geometry_columns
        where ?=?
        order by f_table_name
        """
        layers = self._fetch_all(query, params=[1,1])
        self._layers = map(lambda l: {"id": l["layer_name"]}, layers)
        return self._layers

    def close_connection(self):
        pass

    def name(self):
        if self.database:
            return self.database
        return self.host

    def min_zoom(self):
        return 0

    def max_zoom(self):
        return 23

    def mask_level(self):
        return None

    def scheme(self):
        return "xyz"

    def bounds(self):
        if not self.vector_layers() or len(self.vector_layers()) == 0:
            return None

        if self._bounds:
            return self._bounds

        query = """
        select ST_Extent(ST_Transform(geom,4326)) AS extent
        from {}
        """.format(self.vector_layers()[0]["id"])
        bounds = self._fetch_one(query)
        if bounds:
            coords = bounds["extent"].replace("BOX(", "").replace(")", "").replace(" ", ",").split(",")
            bounds = map(lambda c: float(c), coords)
        return bounds

    def bounds_tile(self, zoom):
        if not self.vector_layers() or len(self.vector_layers()) == 0:
            return None

        bounds = self.bounds()
        return get_tile_bounds(zoom, bounds)

    def crs(self):
        return 3857

    def _get_geom_column(self):
        name = None
        query = """
            SELECT f_geometry_column
            FROM geometry_columns 
            WHERE f_table_name = '{}'
            LIMIT 1
        """.format(self.table_name)
        self._cursor.execute(query)
        res = self._cursor.fetchone()
        if res:
            name = res[0]
        if not name:
            raise "No geometry column found in table '{}'".format(self.table)
        return name

    def _fetch_one(self, sql, params=None, binary_result=False):
        result = None
        rows = self._fetch_all(sql, params, binary_result)
        if rows and len(rows) > 0:
            result = rows[0]
        return result

    def _fetch_all(self, sql, params=None, binary_result=False):
        if not params:
            params = ()

        query = QSqlQuery(self._db)
        query.prepare(sql)
        if not query:
            info("Database Error: {}", self.db.lastError().text())

        for index, p in enumerate(params):
            query.bindValue(index, p)
        query.exec_()
        rows = []
        while query.next():
            obj = {}
            nr_fields = query.record().count()
            for i in range(0, nr_fields):
                val = query.value(i)
                if binary_result:
                    val = bytes(val)
                obj[query.record().fieldName(i)] = val
            rows.append(obj)
        query.finish()
        return rows


class MBTilesSource(AbstractSource):
    def __init__(self, path):
        AbstractSource.__init__(self)
        if not os.path.isfile(path):
            raise RuntimeError("The file does not exist: {}".format(path))

        if not is_sqlite_db(path):
            raise RuntimeError(
                "The file '{}' is not a valid Mapbox vector tile file and cannot be loaded.".format(path))

        self.path = path
        self.conn = None
        self._metadata_cache = {}

    def source(self):
        return self.path

    def crs(self):
        return self._get_metadata_value("crs", _DEFAULT_CRS)

    def vector_layers(self):
        data = self._get_metadata_value("json")
        layers = []
        if data:
            json_data = json.loads(data)
            if "vector_layers" in json_data:
                layers = json_data["vector_layers"]
        return layers

    def bounds_tile(self, zoom):
        bounds = self._get_metadata_value("bounds")
        if bounds:
            bounds = bounds\
                .replace(" ", "")\
                .replace("[", "")\
                .replace("]", "")\
                .split(",")
            bounds = [float(s) for s in bounds]
        scheme = self.scheme()
        return get_tile_bounds(zoom=zoom, bounds=bounds, scheme=scheme)

    def name(self):
        base_name = os.path.splitext(os.path.basename(self.path))[0]
        return base_name

    def scheme(self):
        return self._get_metadata_value("scheme", default="tms")

    def min_zoom(self):
        return self._get_zoom(max_zoom=False)

    def max_zoom(self):
        return self._get_zoom(max_zoom=True)

    def mask_level(self):
        return self._get_metadata_value("maskLevel")

    def load_tiles(self, zoom_level, tiles_to_load, max_tiles=None):
        self._cancelling = False
        debug("Reading tiles of zoom level {}", zoom_level)

        if max_tiles:
            center_tiles = get_tiles_from_center(nr_of_tiles=max_tiles,
                                                 available_tiles=tiles_to_load,
                                                 should_cancel_func=lambda: self._cancelling)
        else:
            center_tiles = tiles_to_load
        where_clause = self._get_where_clause(tiles_to_load=center_tiles, zoom_level=zoom_level)

        sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles {};"
        sql = sql_command.format(where_clause)

        tile_data_tuples = []
        rows = self._get_from_db(sql=sql)
        no_tiles_in_current_extent = not rows or len(rows) == 0
        if no_tiles_in_current_extent:
            where_clause = self._get_where_clause(tiles_to_load=None, zoom_level=zoom_level)
            sql = sql_command.format(where_clause)
            rows = self._get_from_db(sql=sql)

        if rows:
            if max_tiles and len(rows) > max_tiles:
                if no_tiles_in_current_extent:
                    rows = rows[:max_tiles]
                if no_tiles_in_current_extent:
                    self.tile_limit_reached.emit()
            self.max_progress_changed.emit(len(rows))
            for index, row in enumerate(rows):
                if self._cancelling or (max_tiles and len(tile_data_tuples) >= max_tiles):
                    break
                tile, data = self._create_tile(row)
                tile_data_tuples.append((tile, data))
                self.progress_changed.emit(index+1)
        return tile_data_tuples

    @staticmethod
    def _get_where_clause(tiles_to_load, zoom_level):
        where_clause = ""
        if zoom_level is not None or tiles_to_load:
            where_clause = "WHERE"
            if zoom_level is not None:
                where_clause += " zoom_level = {}".format(zoom_level)
                if tiles_to_load:
                    where_clause += " AND"
            if tiles_to_load:
                tile_coords = str(["{};{}".format(x[0], x[1]) for x in tiles_to_load]).replace("[", "").replace(
                    "]", "")
                where_clause += " tile_column || \";\" || tile_row IN ({})".format(tile_coords)
        return where_clause

    def _create_tile(self, row):
        zoom_level = row["zoom_level"]
        tile_col = row["tile_column"]
        tile_row = row["tile_row"]
        binary_data = row["tile_data"]
        tile = VectorTile(self.scheme(), zoom_level, tile_col, tile_row)
        return tile, binary_data

    def close_connection(self):
        """
         * Closes the current db connection
        :return: 
        """
        if self.conn:
            try:
                self.conn.close()
                debug("Connection closed")
            except:
                warn("Closing connection failed: {}".format(sys.exc_info()))
        self.conn = None

    def _get_zoom(self, max_zoom=True):
        if max_zoom:
            field_name = "maxzoom"
        else:
            field_name = "minzoom"

        if field_name not in self._metadata_cache:
            zoom = self._get_metadata_value(field_name)
            if zoom is None:
                zoom = self._get_zoom_from_tiles_table(max_zoom=max_zoom)
            if zoom is not None:
                zoom = int(zoom)
            self._metadata_cache[field_name] = zoom
        return self._metadata_cache[field_name]

    def _get_zoom_from_tiles_table(self, max_zoom=True):
        if max_zoom:
            order = "desc"
        else:
            order = "asc"

        query = ("select zoom_level as 'zoom_level'"
                 "from tiles"
                 "order by zoom_level {}"
                 "limit 1").format(order)
        return self._get_single_value(sql_query=query, field_name="zoom_level")

    def _get_metadata_value(self, field_name, default=None):
        if field_name not in self._metadata_cache:
            debug("Loading metadata value '{}'", field_name)
            sql = "select value as '{0}' from metadata where name = '{0}'".format(field_name)
            value = self._get_single_value(sql_query=sql, field_name=field_name)
            if default and not value:
                value = default
            self._metadata_cache[field_name] = value
        return self._metadata_cache[field_name]

    def _get_single_value(self, sql_query, field_name):
        """
         * Helper function that can be used to safely load a single value from the db
         * Returns the value or None if result is empty or execution of query failed
        :param sql_query: 
        :param field_name: 
        :return: 
        """
        value = None
        try:
            rows = self._get_from_db(sql=sql_query)
            if rows:
                value = rows[0][field_name]
                debug("Value is: {}".format(value))
        except:
            critical("Loading metadata value '{}' failed: {}", field_name, sys.exc_info())
        return value

    def _get_from_db(self, sql):
        if not self.conn:
            debug("Not connected yet.")
            self._connect_to_db()
        try:
            debug("Execute SQL: {}", sql)
            cur = self.conn.cursor()
            cur.execute(sql)
            return cur.fetchall()
        except:
            critical("Getting data from db failed: {}", sys.exc_info())

    def _connect_to_db(self):
        """
         * Since an mbtile file is a sqlite database, we can connect to it
        """
        debug("Connecting to: {}", self.path)
        try:
            self.conn = sqlite3.connect(self.path)
            self.conn.row_factory = sqlite3.Row
            debug("Successfully connected")
        except:
            critical("Db connection failed:", sys.exc_info())


class TrexCacheSource(AbstractSource):
    def __init__(self, path):
        AbstractSource.__init__(self)
        if not os.path.isdir(path):
            raise RuntimeError("The folder does not exist: {}".format(path))
        self.path = path
        metadata_path = os.path.join(path, "metadata.json")
        self.json = TileJSON(metadata_path)
        self.json.load()

    def source(self):
        return self.path

    def vector_layers(self):
        data = json.loads(self.json.get_value("json"))["vector_layers"]
        return data

    def name(self):
        name = self.json.name()
        if not name:
            name = self.json.id()
        if not name:
            name = os.path.basename(self.path)
        return name

    def min_zoom(self):
        return self.json.min_zoom()

    def max_zoom(self):
        return self.json.max_zoom()

    def mask_level(self):
        return self.json.mask_level()

    def scheme(self):
        return self.json.scheme()

    def bounds_tile(self, zoom):
        return self.json.bounds_tile(zoom)

    def crs(self):
        return self.json.crs()

    def load_tiles(self, zoom_level, tiles_to_load, max_tiles=None):
        self._cancelling = False
        tile_data_tuples = []

        if len(tiles_to_load) > max_tiles:
            tiles_to_load = get_tiles_from_center(max_tiles, tiles_to_load, should_cancel_func=lambda: self._cancelling)
            self.tile_limit_reached.emit()

        self.max_progress_changed.emit(tiles_to_load)
        for index, t in enumerate(tiles_to_load):
            self.progress_changed.emit(index)
            tile_path = "{}/{}/{}.pbf".format(int(zoom_level), t[0], t[1])
            full_path = os.path.join(self.path, tile_path)
            col = t[0]
            row = t[1]
            tile = VectorTile(self.scheme(), zoom_level, col, row)
            if os.path.isfile(full_path):
                with open(full_path, 'rb') as f:
                    encoded_data = f.read()
                    tile_data_tuples.append((tile, encoded_data))
        return tile_data_tuples
