import os
import glob
import uuid
import tempfile
import sys
import cPickle as pickle
import time
from log_helper import info, critical, warn, debug


geojson_folder = "geojson"
max_cache_age_minutes = 1440  # 24 hours


def get_plugin_directory():
    return os.path.abspath(os.path.dirname(__file__))


def paths_equal(path1, path2):
    return _normalize_path(path1) == _normalize_path(path2)


def _normalize_path(path):
    path = os.path.normpath(os.path.abspath(path))
    if sys.platform.startswith("win32"):
        try:
            from ctypes import create_unicode_buffer, windll
            BUFFER_SIZE = 500
            buffer = create_unicode_buffer(BUFFER_SIZE)
            get_long_path_name = windll.kernel32.GetLongPathNameW
            get_long_path_name(unicode(path), buffer, BUFFER_SIZE)
            path = os.path.normpath(buffer.value)
        except:
            info("failed: {}", sys.exc_info()[1])
    return path


def get_styles():
    folder = os.path.join(get_plugin_directory(), "styles")
    styles = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    return styles


def get_icons_directory():
    return os.path.join(get_plugin_directory(), "styles", "icons")


def get_cache_directory():
    return get_temp_dir("cache")


def get_cached_tile(file_name):
    file_path = os.path.join(get_cache_directory(), file_name)
    tile = None
    try:
        if os.path.exists(file_path):
            age_in_seconds = int(time.time()) - os.path.getmtime(file_path)
            is_deprecated = age_in_seconds > max_cache_age_minutes * 60
            if is_deprecated:
                os.remove(file_path)
            else:
                with open(file_path, 'rb') as f:
                    tile = pickle.load(f)
    except:
        debug("Error while reading cache entry {}: {}", file_name, sys.exc_info()[1])
    return tile


def get_cached_tile_file_name(source_name, zoom_level, col, row):
    return "{}.{}.{}.{}.bin".format(source_name, zoom_level, col, row)


def cache_tile(tile, source_name):
    cache_file_name = get_cached_tile_file_name(source_name=source_name,
                                                zoom_level=tile.zoom_level,
                                                col=tile.column,
                                                row=tile.row)
    file_path = os.path.join(get_cache_directory(), cache_file_name)
    if not os.path.isfile(file_path):
        if not tile.decoded_data:
            warn("Trying to cache a tile without data: {}", tile)

        try:
            with open(file_path, 'wb') as f:
                pickle.dump(tile, f, pickle.HIGHEST_PROTOCOL)
        except:
            critical("Error while writing tile '{}' to cache: {}", str(tile), sys.exc_info()[1])


def get_sample_data_directory():
    return os.path.join(get_plugin_directory(), "sample_data")


def get_home_directory():
    return os.path.expanduser("~")


def get_temp_dir(path_extension=None):
    temp_dir = os.path.join(tempfile.gettempdir(), "vector_tiles_reader")
    if path_extension:
        temp_dir = os.path.join(temp_dir, path_extension)

    return temp_dir


def clear_cache():
    """
     * Removes all files from the cache
    """
    cache = os.path.join(get_cache_directory())
    if not os.path.exists(cache):
        return
    files = glob.glob(os.path.join(cache, "*"))
    for f in files:
        try:
            os.remove(f)
        except:
            warn("File could not be deleted: {}", f)
    info("Cache cleared")


def assure_temp_dirs_exist():
    _assure_dir_exists(get_temp_dir())
    _assure_dir_exists(get_temp_dir(geojson_folder))
    _assure_dir_exists(get_cache_directory())


def _assure_dir_exists(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def get_geojson_file_name(name):
    path = os.path.join(get_temp_dir(), geojson_folder)
    name_with_extension = "{}.{}".format(name, "geojson")
    return os.path.join(path, name_with_extension)


def get_unique_geojson_file_name():
    path = os.path.join(get_temp_dir(), geojson_folder)
    unique_name = "{}.{}".format(uuid.uuid4(), "geojson")
    return os.path.join(path, unique_name)


def is_sqlite_db(path):
    header_string = "SQLite"
    chunksize = len(header_string)
    with open(path, "r") as f:
        content = f.read(chunksize)
    expected_header = bytearray("SQLite")
    header_matching = are_headers_equal(content, expected_header)
    return header_matching


def is_gzipped(content):
    result = False
    if content and len(content) >= 2:
        gzip_headers = bytearray([0x1f, 0x8b])
        first_two_bytes = bytearray([content[0], content[1]])
        result = are_headers_equal(first_two_bytes, expected_header_bytes=gzip_headers)
    return result


def are_headers_equal(content, expected_header_bytes):
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
