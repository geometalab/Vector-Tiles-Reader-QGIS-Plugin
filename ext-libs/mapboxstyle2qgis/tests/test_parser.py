import os
import sys
import shutil
import json
from xml.sax.saxutils import unescape
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import *
from core import _create_icons


def test_icon_creation():
    image_data = _load_file(os.path.join(os.path.dirname(__file__), "..", "sample_data", "sprite.png"), binary=True)
    image_data = base64.b64encode(image_data)
    image_definition_data = _load_file(os.path.join(os.path.dirname(__file__), "..", "sample_data", "sprite.json"))
    image_definition_data = json.loads(str(image_definition_data))
    output_directory = os.path.join(os.path.dirname(__file__), "generated")
    _create_icons(image_data, image_definition_data, output_directory=output_directory)


def test_generate_qgis():
    # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "roman_empire.json")
    # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "osm_bright.json")
    # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "klokantech_terrain.json")
    # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "klokantech_basic.json")
    # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "positron.json")
    path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "mapcat.json")
    # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "new_style.json")
    data = _load_file(path)
    data = json.loads(data)
    output_directory = r"C:\Users\Martin\AppData\Local\Temp\vector_tiles_reader\styles\mapcat"
    if os.path.isdir(output_directory):
        shutil.rmtree(output_directory)
    generate_styles(data, output_directory)


def test_generate_local():
    # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "roman_empire.json")
    # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "osm_bright.json")
    # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "klokantech_terrain.json")
    # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "klokantech_basic.json")
    # path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "positron.json")
    path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "mapcat.json")
    data = _load_file(path)
    data = json.loads(data)
    output_directory = os.path.join(os.path.dirname(__file__), "generated")
    if os.path.isdir(output_directory):
        shutil.rmtree(output_directory)
    styles = process(data)
    generate_styles(data, output_directory)


def test_filter():
    path = os.path.join(os.path.dirname(__file__), "..", "sample_data", "with_filter.json")
    data = _load_file(path)
    style_obj = process(data)
    styles = style_obj["landuse_overlay.polygon.qml"]["styles"]
    assert len(styles) == 1
    assert "rule" in styles[0]
    assert unescape(styles[0]["rule"], entities={"&quot;": '"'}) == "\"class\" is not null and \"class\" = \'national_park\'"


def _load_file(path, binary=False):
    mode = 'r'
    if binary:
        mode = 'rb'
    with open(path, mode) as f:
        data = f.read()
    return data
