import os
import glob
import uuid
import urllib2
import tempfile
from log_helper import critical, warn


class FileHelper:

    geojson_folder = "geojson"

    def __init__(self):
        pass

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
    def get_home_directory():
        return os.path.expanduser("~")

    @staticmethod
    def get_temp_dir(path_extension=None):
        temp_dir = os.path.join(tempfile.gettempdir(), "vtreader")
        if path_extension:
            temp_dir = os.path.join(temp_dir, path_extension)

        return temp_dir

    @staticmethod
    def clear_cache():
        """
         * Removes all files from the temp_dir
        """
        temp_dir = os.path.join(FileHelper.get_temp_dir(), FileHelper.geojson_folder)
        if not os.path.exists(temp_dir):
            return
        files = glob.glob(os.path.join(temp_dir, "*"))
        for f in files:
            try:
                    os.remove(f)
            except:
                warn("File could not be deleted: {}", f)

    @staticmethod
    def load_url(url, size=None, result_queue=None, params=None):
        """
         * Reads the content of the specified url. If the size parameter is set, only so many bytes will be read
        :param params: This values will be appended to the resulting content
        :param result_queue: A Queue object to append the resulting content to
        :param url: The url to load 
        :param size: The nr of bytes to read, None if all should be read
        :return: 
        """
        req = urllib2.Request(url, headers={'User-Agent': "Magic Browser"})
        content = None
        try:
            response = urllib2.urlopen(req)
            content = response.read(size)
        except urllib2.HTTPError as e:
            critical("Opening url failed with error code '{}': {}", e.code, url)
        except urllib2.URLError:
            critical("The URL seems to be invalid: {}", url)
        if result_queue:
            res = [content, params]
            result_queue.put(res)
        return content

    @staticmethod
    def assure_temp_dirs_exist():
        FileHelper._assure_dir_exists(FileHelper.get_temp_dir())
        FileHelper._assure_dir_exists(FileHelper.get_temp_dir(FileHelper.geojson_folder))

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
