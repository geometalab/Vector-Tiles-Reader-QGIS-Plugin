# -*- coding: utf-8 -*-
#
# This code is licensed under the GPL 2.0 license.
#
from qgis.testing import unittest
import sys
from qgis.utils import iface  # noqa # dont remove! is required for testing (iface wont be found otherwise)
from plugin.vt_reader import VtReader
from plugin.util.connection import MBTILES_CONNECTION_TEMPLATE
import copy
import mock
import shutil
from osgeo import gdal
from plugin.util.file_helper import clear_cache, get_style_folder
from plugin.util.tile_helper import Bounds
from qgis.core import QgsProject
from PyQt5.QtWidgets import QApplication
import os
import time


class VtReaderTests(unittest.TestCase):
    """
    Tests for Iface
    """

    CONNECTION_NAME = "test_conn"

    @classmethod
    def setUpClass(cls):
        src = os.path.join(os.path.dirname(__file__), "data", "styles")
        trg = get_style_folder(cls.CONNECTION_NAME)
        if os.path.isdir(trg):
            shutil.rmtree(trg)
        shutil.copytree(src, trg)

    @classmethod
    def tearDownClass(cls):
        pass

    def testIfaceisNotNone(self):
        global iface
        self.assertIsNotNone(iface)

    @mock.patch("plugin.vt_reader.info")
    @mock.patch("plugin.vt_reader.critical")
    @mock.patch("qgis.core.QgsVectorLayer.loadNamedStyle")
    def test_load_from_vtreader_0_apply_styles(self, mock_style, mock_critical, mock_info):
        global iface
        clear_cache()
        QgsProject.instance().removeAllMapLayers()
        self._load(iface=iface, max_tiles=1, apply_styles=True)
        print(mock_info.call_args_list)
        print(mock_critical.call_args_list)
        # print mock_style.assert_called_with()
        mock_info.assert_any_call("Import complete")

    @mock.patch("plugin.vt_reader.info")
    @mock.patch("plugin.vt_reader.native_decoding_supported", return_value=False)
    @mock.patch.object(VtReader, "_create_qgis_layers")
    def test_load_from_vtreader_0_python_processing(self, mock_qgis, mock_load_lib, mock_info):
        global iface
        QgsProject.instance().removeAllMapLayers()
        clear_cache()

        self._load(iface=iface, max_tiles=1)

        print("calls: ", mock_info.call_args_list)
        mock_info.assert_any_call("Native decoding not supported. ({}, {}bit)", "Linux", "64")
        mock_info.assert_any_call("Decoding finished, {} tiles with data", 1)
        mock_info.assert_any_call("Import complete")

    @mock.patch("plugin.vt_reader.info")
    @mock.patch.object(VtReader, "_create_qgis_layers")
    def test_load_from_vtreader_1_multiprocessed(self, mock_qgis, mock_info):
        global iface
        QgsProject.instance().removeAllMapLayers()
        clear_cache()

        self._load(iface=iface, max_tiles=2, serial_tile_processing_limit=1)

        print(mock_info.call_args_list)
        mock_info.assert_any_call("Native decoding supported!!! ({}, {}bit)", "Linux", "64")
        mock_info.assert_any_call("Processing tiles in parallel...")
        mock_info.assert_any_call("Decoding finished, {} tiles with data", 2)
        mock_info.assert_any_call("Import complete")

    @mock.patch("plugin.vt_reader.info")
    @mock.patch("plugin.util.mp_helper.info")
    def test_load_from_vtreader_2(self, mphelper_mock_info, mock_info):
        global iface
        clear_cache()
        QgsProject.instance().removeAllMapLayers()
        self._load(iface=iface, max_tiles=1)
        print(mock_info.call_args_list)
        print(mphelper_mock_info.call_args_list)
        mock_info.assert_any_call("Native decoding supported!!! ({}, {}bit)", "Linux", "64")
        mock_info.assert_any_call("Decoding finished, {} tiles with data", 1)
        mock_info.assert_any_call("Import complete")

    @mock.patch("plugin.vt_reader.info")
    @mock.patch("plugin.vt_reader.critical")
    def test_load_from_vtreader_3_with_cache(self, mock_critical, mock_info):
        global iface
        self._load(iface=iface, max_tiles=1)
        print(mock_info.call_args_list)
        print(mock_critical.call_args_list)
        mock_info.assert_any_call("Native decoding supported!!! ({}, {}bit)", "Linux", "64")
        mock_info.assert_any_call("{} tiles in cache. Max. {} will be loaded additionally.", 1, 0)
        mock_info.assert_any_call("Import complete")

    @mock.patch("plugin.vt_reader.info")
    @mock.patch("plugin.vt_reader.critical")
    def test_load_from_vtreader_4_merge_native_decoded_tiles(self, mock_critical, mock_info):
        global iface
        clear_cache()
        self._load(iface=iface, max_tiles=2, merge_tiles=True)
        print(mock_info.call_args_list)
        print(mock_critical.call_args_list)
        mock_info.assert_any_call("Native decoding supported!!! ({}, {}bit)", "Linux", "64")
        mock_info.assert_any_call("Import complete")

    @mock.patch("plugin.vt_reader.info")
    @mock.patch("plugin.vt_reader.critical")
    def test_load_from_vtreader_5_clip_native_decoded_tiles(self, mock_critical, mock_info):
        global iface
        clear_cache()
        self._load(iface=iface, max_tiles=2, clip_tiles=True)
        print(mock_info.call_args_list)
        print(mock_critical.call_args_list)
        mock_info.assert_any_call("Native decoding supported!!! ({}, {}bit)", "Linux", "64")
        mock_info.assert_any_call("Import complete")

    @mock.patch("plugin.vt_reader.info")
    @mock.patch("plugin.vt_reader.critical")
    @mock.patch("plugin.vt_reader.native_decoding_supported", return_value=False)
    def test_load_from_vtreader_6_merge_python_decoded_tiles(self, mock_load_lib, mock_critical, mock_info):
        global iface
        clear_cache()
        self._load(iface=iface, max_tiles=2, merge_tiles=True)
        print(mock_info.call_args_list)
        print(mock_critical.call_args_list)
        mock_info.assert_any_call("Native decoding not supported. ({}, {}bit)", "Linux", "64")
        mock_info.assert_any_call("Import complete")

    @mock.patch("plugin.vt_reader.info")
    @mock.patch("plugin.vt_reader.critical")
    @mock.patch("plugin.vt_reader.native_decoding_supported", return_value=False)
    def test_load_from_vtreader_7_clip_python_decoded_tiles(self, mock_load_lib, mock_critical, mock_info):
        global iface
        clear_cache()

        # def wait_for_singal(reader: VtReader):
        #     return QSignalSpy(reader.ready_for_next_loading_step)

        self._load(iface=iface, max_tiles=2, clip_tiles=True)
        # print("Spy isValid:", spy.isValid())
        # print("Spy wait return value: {}".format(spy.wait(timeout=15000)))
        print(mock_info.call_args_list)
        print(mock_critical.call_args_list)
        mock_info.assert_any_call("Native decoding not supported. ({}, {}bit)", "Linux", "64")
        mock_info.assert_any_call("Import complete")

    def _load(
        self,
        iface,
        max_tiles: int,
        serial_tile_processing_limit: int = None,
        merge_tiles: bool = False,
        clip_tiles: bool = False,
        apply_styles: bool = False,
    ):
        conn = copy.deepcopy(MBTILES_CONNECTION_TEMPLATE)
        gdal.PushErrorHandler("CPLQuietErrorHandler")
        conn["name"] = self.CONNECTION_NAME
        conn["path"] = os.path.join(os.path.dirname(__file__), "..", "sample_data", "uster_zh.mbtiles")
        reader = VtReader(iface=iface, connection=conn)
        bounds = Bounds.create(zoom=14, x_min=8587, x_max=8589, y_min=10644, y_max=10645, scheme="xyz")
        reader.set_options(
            merge_tiles=merge_tiles,
            clip_tiles=clip_tiles,
            max_tiles=max_tiles,
            layer_filter=["landcover", "place", "water_name"],
            apply_styles=apply_styles,
        )

        reader._loading_options["zoom_level"] = 14
        reader._loading_options["bounds"] = bounds
        if serial_tile_processing_limit:
            reader._nr_tiles_to_process_serial = serial_tile_processing_limit
        reader._load_tiles()
        for _ in range(1, 100):
            time.sleep(0.01)
            QApplication.processEvents()
        # reader.shutdown()


def suite():
    suite = unittest.makeSuite(VtReaderTests, "test")
    return suite


# run all tests using unittest skipping nose or testplugin
def run_all():
    unittest.TextTestRunner(verbosity=3, stream=sys.stdout).run(suite())


if __name__ == "__main__":
    run_all()
