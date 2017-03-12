import os
import glob
import uuid
import sys


class FileHelper:

    def __init__(self):
        pass

    @staticmethod
    def get_temp_dir():
        directory = os.path.abspath(os.path.dirname(__file__))
        temp_dir = "{}\\tmp".format(directory)
        return temp_dir

    @staticmethod
    def clear_temp_dir():
        """
         * Removes all files from the temp_dir
        """
        temp_dir = FileHelper.get_temp_dir()
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        files = glob.glob("{}\\*".format(temp_dir))
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
