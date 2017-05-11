import os
import sys
import sqlite3
import threading
import urlparse
import Queue
import json

from log_helper import debug, critical, warn, info
from tile_json import TileJSON
from file_helper import FileHelper
from tile_helper import VectorTile, get_all_tiles


_DEFAULT_CRS = "EPSG:3857"

class ServerSource:
    def __init__(self, url):
        if not url:
            raise RuntimeError("URL is required")

        valid, error = FileHelper.url_exists(url)
        if not valid:
            raise RuntimeError(error)

        self.url = url
        is_web_source = url.lower().startswith("http://") or url.lower().startswith("https://")
        if not is_web_source:
            raise RuntimeError("The URL is invalid: {}".format(url))

        self.json = TileJSON(url)
        self.json.load()
        self._progress_handler = None
        self._cancelling = False

    def _validate_url(self, url):
        try:
            urllib2.urlopen('http://www.example.com/some_page')
        except urllib2.HTTPError, e:
            print(e.code)
        except urllib2.URLError, e:
            print(e.args)

    def cancel(self):
        self._cancelling = True

    def set_progress_handler(self, func):
        self._progress_handler = func

    def source(self):
        return self.url

    def attribution(self):
        return self.json.attribution()

    def vector_layers(self):
        return self.json.vector_layers()

    def name(self):
        name = self.json.name()
        if not name:
            name = self.json.id()
        if not name:
            name = urlparse.urlsplit(self.url)[1]
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

    def load_tiles(self, zoom_level, bounds=None, max_tiles=None, for_each=None, limit_reacher_handler=None):
        """
         * Loads the tiles for the specified zoom_level and bounds from the web service this source has been created with
        :param zoom_level: The zoom level which will be loaded
        :param bounds: If set, only tiles inside this tile boundary will be loaded
        :param max_tiles: The maximum number of tiles to be loaded
        :param for_each: A function which will be called for every row
        :param limit_reacher_handler: A function which will be called, if the potential nr of tiles is greater than the specified limit
        :return: 
        """

        self._cancelling = False
        base_url = self.json.tiles()[0]
        tiles_to_load = get_all_tiles(bounds)
        tile_data_tuples = []
        urls = []

        if len(tiles_to_load) > max_tiles:
            tiles_to_load = tiles_to_load[:max_tiles]
            if limit_reacher_handler:
                limit_reacher_handler()

        for t in tiles_to_load:
            col = t[0]
            row = t[1]
            load_url = base_url\
                .replace("{z}", str(zoom_level))\
                .replace("{x}", str(col))\
                .replace("{y}", str(row))
            urls.append((load_url, col, row))

        self._progress_handler(msg="Getting {} tiles from source...".format(len(urls)), max_progress=len(urls))
        queue = Queue.Queue()

        page_size = 5
        self._do_paged(page_size, urls, self._load_urls_async, queue, for_each)

        while not queue.empty():
            r = queue.get()
            content = r[0]
            col = r[1][0]
            row = r[1][1]
            tile = VectorTile(self.scheme(), zoom_level, col, row)
            tile_data_tuples.append((tile, content))

        return tile_data_tuples

    def _load_urls_async(self, page_offset, urls, *args):
        queue = args[0]
        for_each = args[1]
        threads = [threading.Thread(
            name="URL-Thread-{}".format(index),
            target=FileHelper.load_url,
            args=(u[0], None, queue, [u[1], u[2]])) for index, u in enumerate(urls)]
        for thread in threads:
            thread.start()
        for index, thread in enumerate(threads):
            if for_each:
                for_each()
            if self._cancelling:
                break
            thread.join()
            self._progress_handler(progress=page_offset+index+1)

    def _do_paged(self, page_size, all_items, func, *args):
        page_nr = 0
        items = []
        while page_nr == 0 or len(items) > 0:
            items = all_items[page_nr:page_nr + page_size]
            if self._cancelling or len(items) == 0:
                break
            page_offset = page_nr*page_size
            func(page_offset, items, *args)
            page_nr += page_size


class MBTilesSource:
    def __init__(self, path):
        if not os.path.isfile(path):
            raise RuntimeError("The file does not exist: {}".format(path))

        is_sqlite_db = FileHelper.is_sqlite_db(path)
        if not is_sqlite_db:
            raise RuntimeError(
                "The file '{}' is not a valid Mapbox vector tile file and cannot be loaded.".format(path))

        self.path = path
        self.conn = None
        self._metadata_cache = {}
        self._progress_handler = None
        self._cancelling = False

    def cancel(self):
        self._cancelling = True

    def set_progress_handler(self, func):
        self._progress_handler = func

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

    def name(self):
        base_name = os.path.splitext(os.path.basename(self.path))[0]
        return base_name

    def scheme(self):
        return self._get_metadata_value("scheme", default="tms")

    def min_zoom(self):
        """
         * Returns the minimum zoom that is found in either the metadata or the tile table
        :return: 
        """
        return self._get_zoom(max_zoom=False)

    def max_zoom(self):
        """
         * Returns the maximum zoom that is found in either the metadata or the tile table
        :return: 
        """
        return self._get_zoom(max_zoom=True)

    def mask_level(self):
        """
         * Returns the mask level from the metadata table
        :return: 
        """
        return self._get_metadata_value("maskLevel")

    def is_mapbox_vector_tile(self):
        """
         * A .mbtiles file is a Mapbox Vector Tile if the binary tile data is gzipped.
        :return:
        """
        debug("Checking if file corresponds to Mapbox format (i.e. gzipped)")
        is_mapbox_pbf = False
        try:
            tile_data_tuples = self.load_tiles(max_tiles=1, zoom_level=None)
            if len(tile_data_tuples) == 1:
                undecoded_data = tile_data_tuples[0][1]
                if undecoded_data:
                    is_mapbox_pbf = FileHelper.is_gzipped(undecoded_data)
                    if is_mapbox_pbf:
                        debug("File is valid mbtiles")
                    else:
                        debug("pbf is not gzipped")
        except:
            warn("Something went wrong. This file doesn't seem to be a Mapbox Vector Tile. {}", sys.exc_info())
        return is_mapbox_pbf

    def load_tiles(self, zoom_level, bounds=None, max_tiles=None, for_each=None, limit_reacher_handler=None):
        """
         * Loads the tiles for the specified zoom_level and bounds from the mbtiles file this source has been created with
        :param zoom_level: The zoom level which will be loaded
        :param bounds: If set, only tiles inside this tile boundary will be loaded
        :param max_tiles: The maximum number of tiles to be loaded
        :param for_each: A function which will be called for every row
        :param limit_reacher_handler: A function which will be called, if the potential nr of tiles is greater than the specified limit
        :return: 
        """

        self._cancelling = False
        info("Reading tiles of zoom level {}", zoom_level)

        where_clause = self._get_where_clause(bounds, zoom_level)
        limit_clause = self._get_limit_clause(max_tiles)

        sql_command = "SELECT zoom_level, tile_column, tile_row, tile_data FROM tiles {} {};"
        sql = sql_command.format(where_clause, limit_clause)

        tile_data_tuples = []
        rows = self._get_from_db(sql=sql)
        if not rows or len(rows) == 0:
            # execute the query again, without a tile_boundary
            where_clause = self._get_where_clause(bounds=None, zoom_level=zoom_level)
            sql = sql_command.format(where_clause, limit_clause)
            rows = self._get_from_db(sql=sql)

        if rows:
            if len(rows) > max_tiles:
                rows = rows[:max_tiles]
                if limit_reacher_handler:
                    limit_reacher_handler()
            self._progress_handler(max_progress=len(rows))
            for index, row in enumerate(rows):
                if for_each:
                    for_each()
                if self._cancelling:
                    break
                tile, data = self._create_tile(row)
                tile_data_tuples.append((tile, data))
                self._progress_handler(progress=index+1)
        return tile_data_tuples

    @staticmethod
    def _get_limit_clause(max_tiles):
        limit = ""
        if max_tiles is not None:
            """
            +1 is added to max_tiles to easily detect if the number of rows is greater than the limit, so that a
            message can be shown to the user.
            """
            limit = "LIMIT {}".format(max_tiles + 1)
        return limit

    @staticmethod
    def _get_where_clause(bounds, zoom_level):
        where_clause = ""
        if zoom_level is not None or bounds:
            where_clause = "WHERE"
            if zoom_level is not None:
                where_clause += " zoom_level = {}".format(zoom_level)
                if bounds:
                    where_clause += " AND"
            if bounds:
                col_min = min(bounds[0][0], bounds[1][0])
                col_max = max(bounds[0][0], bounds[1][0])
                row_min = min(bounds[0][1], bounds[1][1])
                row_max = max(bounds[0][1], bounds[1][1])
                where_clause += " tile_column BETWEEN {} AND {}".format(col_min, col_max)
                where_clause += " and tile_row BETWEEN {} AND {}".format(row_min, row_max)
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
            critical("Getting data from db failed:", sys.exc_info())

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
