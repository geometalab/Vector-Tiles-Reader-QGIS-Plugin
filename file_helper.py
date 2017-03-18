import os
import glob
import uuid
import sys


class FileHelper:

    recently_used_filename = "data.bin"

    def __init__(self):
        pass

    @staticmethod
    def get_recently_used_file():
        path = os.path.join(FileHelper.get_data_dir(), FileHelper.recently_used_filename)
        return path

    @staticmethod
    def get_directory():
        return os.path.abspath(os.path.dirname(__file__))

    @staticmethod
    def get_data_dir():
        dir = FileHelper.get_directory()
        return os.path.join(dir, "data")

    @staticmethod
    def get_temp_dir():
        directory = FileHelper.get_data_dir()
        temp_dir = os.path.join(directory, "tmp")
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
            print("A file could not be deleted: {}".format(sys.exc_info()))

    @staticmethod
    def get_unique_file_name(ending="geojson"):
        temp_dir = FileHelper.get_temp_dir()
        unique_name = "{}.{}".format(uuid.uuid4(), ending)
        return os.path.join(temp_dir, unique_name)
