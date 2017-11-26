# -*- coding: utf-8 -*-
#
# This code is licensed under the GPL 2.0 license.
#
import unittest
import os
import sys
from qgis.core import *
from qgis.utils import iface
from PyQt4.QtCore import *
from vt_reader import VtReader
from util.connection import MBTILES_CONNECTION_TEMPLATE
import copy
import mock
from osgeo import gdal
from util.file_helper import clear_cache


class VtReaderTests(unittest.TestCase):
    """
    Tests for Iface
    """

    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def testIfaceisNotNone(self):
        global iface
        self.assertIsNotNone(iface)

    @mock.patch("vt_reader.info")
    @mock.patch("vt_reader.can_load_lib", return_value=False)
    @mock.patch.object(VtReader, "_create_qgis_layers")
    def test_load_from_vtreader_0_python_processing(self, mock_qgis, mock_can_load_lib, mock_info):
        global iface
        QgsMapLayerRegistry.instance().removeAllMapLayers()
        clear_cache()

        self._load(iface=iface, max_tiles=1)

        print mock_info.call_args_list
        mock_info.assert_any_call('Native decoding not supported: {}, {}bit', 'linux2', '64')
        mock_info.assert_any_call("Decoding finished, {} tiles with data", 1)
        mock_info.assert_any_call("Import complete")

    @mock.patch("vt_reader.info")
    @mock.patch.object(VtReader, "_create_qgis_layers")
    def test_load_from_vtreader_1_multiprocessed(self, mock_qgis, mock_info):
        global iface
        QgsMapLayerRegistry.instance().removeAllMapLayers()
        clear_cache()

        self._load(iface=iface, max_tiles=2, serial_tile_processing_limit=1)

        print mock_info.call_args_list
        mock_info.assert_any_call("Native decoding supported!!!")
        mock_info.assert_any_call("Decoding finished, {} tiles with data", 2)
        mock_info.assert_any_call("Import complete")

    @mock.patch("vt_reader.info")
    def test_load_from_vtreader_2(self, mock_info):
        global iface
        clear_cache()
        QgsMapLayerRegistry.instance().removeAllMapLayers()
        self._load(iface=iface, max_tiles=1)
        print mock_info.call_args_list
        mock_info.assert_any_call("Native decoding supported!!!")
        mock_info.assert_any_call("Decoding finished, {} tiles with data", 1)
        mock_info.assert_any_call("Import complete")

    @mock.patch("vt_reader.info")
    @mock.patch("vt_reader.critical")
    def test_load_from_vtreader_3_with_cache(self, mock_critical, mock_info):
        global iface
        self._load(iface=iface, max_tiles=1)
        print mock_info.call_args_list
        print mock_critical.call_args_list
        mock_info.assert_any_call("Native decoding supported!!!")
        mock_info.assert_any_call("{} tiles in cache. Max. {} will be loaded additionally.", 1, 0)
        mock_info.assert_any_call("Import complete")

    @mock.patch("vt_reader.info")
    @mock.patch("vt_reader.critical")
    def test_load_from_vtreader_4_merge_native_decoded_tiles(self, mock_critical, mock_info):
        global iface
        clear_cache()
        self._load(iface=iface, max_tiles=2, merge_tiles=True)
        print mock_info.call_args_list
        print mock_critical.call_args_list
        mock_info.assert_any_call("Native decoding supported!!!")
        mock_info.assert_any_call("Import complete")

    @mock.patch("vt_reader.info")
    @mock.patch("vt_reader.critical")
    def test_load_from_vtreader_5_clip_native_decoded_tiles(self, mock_critical, mock_info):
        global iface
        clear_cache()
        self._load(iface=iface, max_tiles=2, clip_tiles=True)
        print mock_info.call_args_list
        print mock_critical.call_args_list
        mock_info.assert_any_call("Native decoding supported!!!")
        mock_info.assert_any_call("Import complete")

    @mock.patch("vt_reader.info")
    @mock.patch("vt_reader.critical")
    @mock.patch("vt_reader.can_load_lib", return_value=False)
    def test_load_from_vtreader_6_merge_python_decoded_tiles(self, mock_can_load, mock_critical, mock_info):
        global iface
        clear_cache()
        self._load(iface=iface, max_tiles=2, merge_tiles=True)
        print mock_info.call_args_list
        print mock_critical.call_args_list
        mock_info.assert_any_call('Native decoding not supported: {}, {}bit', 'linux2', '64')
        mock_info.assert_any_call("Import complete")

    @mock.patch("vt_reader.info")
    @mock.patch("vt_reader.critical")
    @mock.patch("vt_reader.can_load_lib", return_value=False)
    def test_load_from_vtreader_7_clip_python_decoded_tiles(self, mock_can_load, mock_critical, mock_info):
        global iface
        clear_cache()
        self._load(iface=iface, max_tiles=2, clip_tiles=True)
        print mock_info.call_args_list
        print mock_critical.call_args_list
        mock_info.assert_any_call('Native decoding not supported: {}, {}bit', 'linux2', '64')
        mock_info.assert_any_call("Import complete")

    def _load(self, iface, max_tiles, serial_tile_processing_limit=None, merge_tiles=False, clip_tiles=False):
        conn = copy.deepcopy(MBTILES_CONNECTION_TEMPLATE)
        gdal.PushErrorHandler('CPLQuietErrorHandler')
        conn["name"] = "Unittest_Connection"
        conn["path"] = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'uster_zh.mbtiles')
        reader = VtReader(iface=iface, connection=conn)
        bounds = {'y_min': 10644, 'y_max': 10645, 'zoom': 14, 'height': 2, 'width': 3, 'x_max': 8589, 'x_min': 8587}
        reader.set_options(max_tiles=max_tiles, layer_filter=['landcover', 'place', 'water_name'], merge_tiles=merge_tiles, clip_tiles=clip_tiles)
        reader._loading_options["zoom_level"] = 14
        reader._loading_options["bounds"] = bounds
        if serial_tile_processing_limit:
            reader._nr_tiles_to_process_serial = serial_tile_processing_limit
        reader._load_tiles()
        reader.shutdown()


def suite():
    suite = unittest.makeSuite(VtReaderTests, 'test')
    return suite


# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())


if __name__ == "__main__":
    run_all()
