import os
import sys
from qgis.testing import unittest
import shutil
import json
import base64
from xml.sax.saxutils import unescape
from plugin.util.file_helper import get_plugin_directory, get_temp_dir
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plugin.style_converter.core import _create_icons, generate_styles, process


class StyleConverterParserTests(unittest.TestCase):
    sample_data_dir = os.path.join(get_plugin_directory(), "style_converter", "sample_data")

    def test_icon_creation(self):

        image_data = self._load_file(os.path.join(self.sample_data_dir, "sprite.png"), binary=True)
        image_data = base64.b64encode(image_data)
        image_definition_data = self._load_file(os.path.join(self.sample_data_dir, "sprite.json"))
        image_definition_data = json.loads(str(image_definition_data))
        output_directory = get_temp_dir(os.path.join("style_converter_tests", "generated"))
        _create_icons(image_data, image_definition_data, output_directory=output_directory)

    def test_generate_local(self):
        # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "roman_empire.json")
        # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "osm_bright.json")
        # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "klokantech_terrain.json")
        # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "klokantech_basic.json")
        # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "positron.json")
        path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "mapcat.json")
        data = self._load_file(path)
        data = json.loads(data)
        output_directory = get_temp_dir(os.path.join("style_converter_tests", "generated"))
        if os.path.isdir(output_directory):
            shutil.rmtree(output_directory)
        styles = process(data)
        generate_styles(data, output_directory)
        self.assertTrue(True)

    def test_filter(self):
        path = os.path.join(self.sample_data_dir, "with_filter.json")
        data = self._load_file(path)
        style_obj = process(data)
        styles = style_obj["landuse_overlay.polygon.qml"]["styles"]
        self.assertEqual(len(styles), 1)
        self.assertIn("rule", styles[0])
        res = unescape(styles[0]["rule"], entities={"&quot;": '"'})
        expected = "\"class\" is not null and \"class\" = \'national_park\'"
        self.assertEqual(expected, res)

    @staticmethod
    def _load_file(path, binary=False):
        mode = 'r'
        if binary:
            mode = 'rb'
        with open(path, mode) as f:
            data = f.read()
        return data
