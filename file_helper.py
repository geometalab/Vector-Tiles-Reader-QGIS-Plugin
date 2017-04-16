import os
import glob
import uuid
import urllib2
import tempfile
from log_helper import critical


class FileHelper:

    geojson_folder = "geojson"

    def __init__(self):
        pass

    @staticmethod
    def get_plugin_directory():
        return os.path.abspath(os.path.dirname(__file__))

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
    def clear_temp_dir():
        """
         * Removes all files from the temp_dir
        """
        temp_dir = FileHelper.get_temp_dir()
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        files = glob.glob(os.path.join(temp_dir, "*"))
        try:
            for f in files:
                os.remove(f)
        except:
            pass

    @staticmethod
    def load_url(url, size=None):
        """
         * Reads the content of the specified url. If the size parameter is set, only so many bytes will be read
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
        if len(content) >= 2:
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
