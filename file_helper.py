import os
import glob
import uuid
import tempfile
import sys
import cPickle as pickle
import time
from log_helper import critical, warn, debug
from qgis.core import QgsNetworkAccessManager

from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QUrl
from PyQt4.QtNetwork import QNetworkRequest


class FileHelper:

    geojson_folder = "geojson"
    max_cache_age_minutes = 1440  # 24 hours

    def __init__(self):
        pass

    @staticmethod
    def url_exists(url):
        status, data = FileHelper.load_url(url)
        result = status == 200
        error = None
        if status != 200:
            error = data

        return result, error

    @staticmethod
    def get_plugin_directory():
        return os.path.abspath(os.path.dirname(__file__))

    @staticmethod
    def get_styles():
        folder = os.path.join(FileHelper.get_plugin_directory(), "styles")
        styles = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        return styles

    @staticmethod
    def get_icons_directory():
        return os.path.join(FileHelper.get_plugin_directory(), "styles", "icons")

    @staticmethod
    def get_cache_directory():
        return FileHelper.get_temp_dir("cache")

    @staticmethod
    def get_cached_tile(file_name):
        file_path = os.path.join(FileHelper.get_cache_directory(), file_name)
        tile = None
        try:
            if os.path.exists(file_path):
                age_in_seconds = int(time.time()) - os.path.getmtime(file_path)
                is_deprecated = age_in_seconds > FileHelper.max_cache_age_minutes * 60
                if is_deprecated:
                    os.remove(file_path)
                else:
                    with open(file_path, 'rb') as f:
                        tile = pickle.load(f)
        except:
            debug("Error while reading cache entry {}: {}", file_name, sys.exc_info()[1])
        return tile

    @staticmethod
    def get_cached_tile_file_name(source_name, zoom_level, col, row):
        return "{}.{}.{}.{}.bin".format(source_name, zoom_level, col, row)

    @staticmethod
    def cache_tile(tile, file_name):
        if not tile.decoded_data:
            warn("Trying to cache a tile without data: {}", tile)

        file_path = os.path.join(FileHelper.get_cache_directory(), file_name)
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(tile, f, pickle.HIGHEST_PROTOCOL)
        except:
            debug("Error while writing tile '{}' to cache", str(tile))

    @staticmethod
    def get_sample_data_directory():
        return os.path.join(FileHelper.get_plugin_directory(), "sample_data")

    @staticmethod
    def get_home_directory():
        return os.path.expanduser("~")

    @staticmethod
    def get_temp_dir(path_extension=None):
        temp_dir = os.path.join(tempfile.gettempdir(), "vector_tiles_reader")
        if path_extension:
            temp_dir = os.path.join(temp_dir, path_extension)

        return temp_dir

    @staticmethod
    def clear_cache():
        """
         * Removes all files from the cache
        """
        cache = os.path.join(FileHelper.get_cache_directory())
        if not os.path.exists(cache):
            return
        files = glob.glob(os.path.join(cache, "*"))
        for f in files:
            try:
                os.remove(f)
            except:
                warn("File could not be deleted: {}", f)

    @staticmethod
    def load_url_async(url):
        m = QgsNetworkAccessManager.instance()
        req = QNetworkRequest(QUrl(url))
        req.setRawHeader('User-Agent', 'Magic Browser')
        reply = m.get(req)
        return reply

    @staticmethod
    def load_url(url):
        reply = FileHelper.load_url_async(url)
        while not reply.isFinished():
            QApplication.processEvents()

        http_status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        if http_status_code == 200:
            content = reply.readAll().data()
        else:
            if http_status_code is None:
                content = "Request failed: {}".format(reply.errorString())
            else:
                content = "Request failed: HTTP status {}".format(http_status_code)
            warn(content)
        return http_status_code, content

    @staticmethod
    def assure_temp_dirs_exist():
        FileHelper._assure_dir_exists(FileHelper.get_temp_dir())
        FileHelper._assure_dir_exists(FileHelper.get_temp_dir(FileHelper.geojson_folder))
        FileHelper._assure_dir_exists(FileHelper.get_cache_directory())

    @staticmethod
    def _assure_dir_exists(path):
        if not os.path.isdir(path):
            os.makedirs(path)

    @staticmethod
    def get_geojson_file_name(name):
        path = os.path.join(FileHelper.get_temp_dir(), FileHelper.geojson_folder)
        name_with_extension = "{}.{}".format(name, "geojson")
        return os.path.join(path, name_with_extension)

    @staticmethod
    def get_unique_geojson_file_name():
        path = os.path.join(FileHelper.get_temp_dir(), FileHelper.geojson_folder)
        unique_name = "{}.{}".format(uuid.uuid4(), "geojson")
        return os.path.join(path, unique_name)

    @staticmethod
    def is_sqlite_db(path):
        header_string = "SQLite"
        chunksize = len(header_string)
        with open(path, "r") as f:
            content = f.read(chunksize)
        expected_header = bytearray("SQLite")
        header_matching = FileHelper._are_headers_equal(content, expected_header)
        return header_matching

    @staticmethod
    def is_gzipped(content):
        result = False
        if content and len(content) >= 2:
            gzip_headers = bytearray([0x1f, 0x8b])
            first_two_bytes = bytearray([content[0], content[1]])
            result = FileHelper._are_headers_equal(first_two_bytes, expected_header_bytes=gzip_headers)
        return result

    @staticmethod
    def _are_headers_equal(content, expected_header_bytes):
        all_same = True
        br = bytearray(content)
        for index, b in enumerate(expected_header_bytes):
            try:
                all_same = br[index] == b
                if not all_same:
                    break
            except IndexError:
                all_same = False
                break
        return all_same