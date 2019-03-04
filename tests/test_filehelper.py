import sys
from qgis.testing import unittest
from util.file_helper import *
from util import file_helper


class FileHelperTests(unittest.TestCase):
    """
    Tests for util.file_helper
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def test_get_plugin_dir(self):
        self.assertEqual('/tests_directory/util/..', get_plugin_directory())

    def test_get_temp_dir(self):
        self.assertEqual('/tmp/vector_tiles_reader', get_temp_dir())

    def test_get_temp_dir_extended(self):
        self.assertEqual('/tmp/vector_tiles_reader/hello/world.txt', get_temp_dir("hello/world.txt"))

    def test_get_styles_dir(self):
        self.assertEqual('/tmp/vector_tiles_reader/styles/my_connection', get_style_folder("my_connection"))

    def test_get_icons_dir(self):
        self.assertEqual('/tests_directory/util/../styles/icons', get_icons_directory())

    def test_get_cache_dir(self):
        self.assertEqual('/tmp/vector_tiles_reader/cache', get_cache_directory())

    def test_get_geojson_filename(self):
        self.assertEqual('/tmp/vector_tiles_reader/tmp/name.geojson', get_geojson_file_name("name"))

    def test_is_sqlite_db_true(self):
        sample_file = os.path.join(get_sample_data_directory(), "uster_zh.mbtiles")
        self.assertTrue(is_sqlite_db(sample_file))

    def test_is_sqlite_false_true(self):
        self.assertFalse(is_sqlite_db(os.path.realpath(__file__)))

    def test_get_sample_dir(self):
        self.assertEqual('/tests_directory/util/../sample_data', get_sample_data_directory())

    def test_create_temp_dirs(self):
        assure_temp_dirs_exist()

    def test_is_gzipped_true(self):
        self.assertTrue(is_gzipped([0x1f, 0x8b]))

    def test_is_gzipped_false(self):
        self.assertFalse(is_gzipped([0xC0, 0xFF, 0xEE]))

    def test_get_styles(self):
        self.assertEqual(0, len(get_styles("total_random_name_that_doesnt_exist")))

    def test_get_cached_tile(self):
        self.assertIsNone(get_cache_entry("blabla", "zoom", "x", "y"))

    def test_get_cached_tile_file_name(self):
        path = os.path.join(get_cache_directory(), "test", "2", "3", "4.bin")
        self.assertEqual(path, file_helper._get_cache_entry_path("test", zoom_level=2, x=3, y=4))


def suite():
    s = unittest.makeSuite(FileHelperTests, 'test')
    return s


# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())


if __name__ == "__main__":
    run_all()
