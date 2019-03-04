import os
import tempfile
import sys
import time
import shutil

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle
from .log_helper import info, critical, warn, debug


geojson_folder = "tmp"
max_cache_age_minutes = 1440  # 24 hours

_temp_dir = tempfile.gettempdir()


def get_plugin_directory():
    path = os.path.join(os.path.dirname(__file__), "..")
    return path


def get_style_folder(connection_name):
    folder = os.path.join(get_temp_dir(), "styles", connection_name)
    return folder


def get_styles(connection_name):
    folder = get_style_folder(connection_name)
    styles = []
    if os.path.isdir(folder):
        styles = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    return styles


def get_icons_directory():
    return os.path.join(get_plugin_directory(), "styles", "icons")


def get_cache_directory():
    return get_temp_dir("cache")


def _get_cache_entry_path(cache_name, zoom_level, x, y):
    return os.path.join(get_cache_directory(), cache_name, str(zoom_level), str(x), "{}.bin".format(y))


def get_cache_entry(cache_name, zoom_level, x, y):
    file_path = _get_cache_entry_path(cache_name=cache_name, zoom_level=zoom_level, x=x, y=y)
    decoded_data = None
    try:
        if os.path.isfile(file_path):
            age_in_seconds = int(time.time()) - os.path.getmtime(file_path)
            is_deprecated = age_in_seconds > max_cache_age_minutes * 60
            if is_deprecated:
                os.remove(file_path)
            else:
                with open(file_path, "rb") as f:
                    decoded_data = pickle.load(f)
    except:
        critical("Error while reading cache entry {}: {}", file_path, sys.exc_info()[1])
    return decoded_data


def cache_tile(cache_name, zoom_level, x, y, decoded_data):
    file_path = _get_cache_entry_path(cache_name=cache_name, zoom_level=zoom_level, x=x, y=y)
    if not os.path.isfile(file_path):
        if not decoded_data:
            warn("Trying to cache a tile without data: {}: {},{},{}", cache_name, zoom_level, x, y)
        else:
            try:
                directory = os.path.dirname(file_path)
                if not os.path.isdir(directory):
                    os.makedirs(directory)
                with open(file_path, "wb") as f:
                    pickle.dump(decoded_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            except:
                critical("Error during caching of '{}': {}", file_path, sys.exc_info()[1])


def get_sample_data_directory():
    return os.path.join(get_plugin_directory(), "sample_data")


def get_temp_dir(path_extension=None):
    temp_dir = os.path.join(_temp_dir, "vector_tiles_reader")
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

    shutil.rmtree(get_cache_directory(), ignore_errors=True)
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


def is_sqlite_db(path):
    header_string = "SQLite"
    chunksize = len(header_string)
    with open(path, "rb+") as f:
        content = f.read(chunksize)
    expected_header = bytearray("SQLite", encoding="UTF-8")
    header_matching = are_headers_equal(content, expected_header)
    return header_matching


def is_gzipped(content):
    result = False
    if content and len(content) >= 2:
        gzip_headers = bytearray([0x1F, 0x8B])
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
