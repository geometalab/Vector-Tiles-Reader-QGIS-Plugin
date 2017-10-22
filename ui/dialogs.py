import os
import webbrowser
import csv
import resources_rc  # don't remove this import, otherwise the icons won't be working

from collections import OrderedDict
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal, QSettings
from PyQt4.QtGui import QFileDialog, QMessageBox, QStandardItemModel, QStandardItem, QApplication
from dlg_connections import Ui_DlgConnections
from dlg_edit_connection import Ui_DlgEditConnection
from dlg_about import Ui_DlgAbout
from dlg_progress import Ui_DlgProgress
from options import Ui_OptionsGroup
from ..log_helper import *


_HELP_URL = "https://giswiki.hsr.ch/Vector_Tiles_Reader_QGIS_Plugin"


def _update_size(dialog, fix_size=False):
    screen_resolution = QApplication.desktop().screenGeometry()
    screen_width, screen_height = screen_resolution.width(), screen_resolution.height()
    if screen_width > 1920 or screen_height > 1080:
        new_width = dialog.width() / 1920.0 * screen_width
        new_height = dialog.height() / 1080.0 * screen_height
        if fix_size:
            dialog.setFixedSize(new_width, new_height)
        else:
            dialog.setMinimumSize(new_width, new_height)


class AboutDialog(QtGui.QDialog, Ui_DlgAbout):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self._load_about()
        _update_size(self)

    def _load_about(self):
        about_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "about.html")
        if os.path.isfile(about_path):
            with open(about_path, 'r') as f:
                html = f.read()
                self.txtAbout.setHtml(html)

    def show(self):
        self.exec_()


class OptionsGroup(QtGui.QGroupBox, Ui_OptionsGroup):

    on_zoom_change = pyqtSignal()

    def __init__(self, target_groupbox, zoom_change_handler):
        super(QtGui.QGroupBox, self).__init__()
        self._zoom_change_handler = zoom_change_handler
        self.setupUi(target_groupbox)
        self.lblZoomRange.setText("")
        self.chkLimitNrOfTiles.toggled.connect(lambda enabled: self.spinNrOfLoadedTiles.setEnabled(enabled))
        self.rbZoomManual.toggled.connect(self._on_manual_zoom_selected)
        self.rbZoomMax.toggled.connect(self._on_max_zoom_selected)
        self.zoomSpin.valueChanged.connect(self._on_zoom_change)
        self.btnResetToBasemapDefaults.clicked.connect(self._reset_to_basemap_defaults)
        self.btnResetToInspectionDefaults.clicked.connect(self._reset_to_inspection_defaults)
        self.btnResetToAnalysisDefaults.clicked.connect(self._reset_to_analysis_defaults)
        self._reset_to_basemap_defaults()

    def _on_manual_zoom_selected(self, enabled):
        self.zoomSpin.setEnabled(enabled)
        self._zoom_change_handler()

    def _on_zoom_change(self):
        self._zoom_change_handler()

    def _on_max_zoom_selected(self, enabled):
        self._zoom_change_handler()

    def set_nr_of_tiles(self, nr_tiles):
        self.lblNumberTilesInCurrentExtent.setText("(Current extent: {} tiles)".format(nr_tiles))

    def _reset_to_basemap_defaults(self):
        self._set_settings(auto_zoom=True, tile_limit=32, styles_enabled=True, merging_enabled=False,
                           clip_tile_at_bounds=True)

    def _reset_to_analysis_defaults(self):
        self._set_settings(auto_zoom=True, tile_limit=10, styles_enabled=False, merging_enabled=True,
                           clip_tile_at_bounds=True)

    def _reset_to_inspection_defaults(self):
        self._set_settings(auto_zoom=False, tile_limit=1, styles_enabled=False, merging_enabled=False,
                           clip_tile_at_bounds=False)

    def _set_settings(self, auto_zoom, tile_limit, styles_enabled, merging_enabled, clip_tile_at_bounds):
        self.rbZoomMax.setChecked(not auto_zoom)
        self.rbAutoZoom.setChecked(auto_zoom)
        tile_limit_enabled = tile_limit is not None
        self.chkLimitNrOfTiles.setChecked(tile_limit_enabled)
        if tile_limit_enabled:
            self.spinNrOfLoadedTiles.setValue(tile_limit)
        self.chkApplyStyles.setChecked(styles_enabled)
        self.chkMergeTiles.setChecked(merging_enabled)
        self.chkClipTiles.setChecked(clip_tile_at_bounds)

    def set_omt_styles_enabled(self, enabled):
        self.chkApplyStyles.setChecked(enabled)

    def set_zoom(self, min_zoom=None, max_zoom=None):
        if min_zoom:
            self.zoomSpin.setMinimum(min_zoom)
        else:
            self.zoomSpin.setMinimum(0)
        max_zoom_text = "Max. Zoom"
        if max_zoom:
            self.zoomSpin.setMaximum(max_zoom)
            max_zoom_text += " ({})".format(max_zoom)
        else:
            self.zoomSpin.setMaximum(99)
        self.rbZoomMax.setText(max_zoom_text)

        zoom_range_text = ""
        if min_zoom or max_zoom:
            zoom_range_text = "({} - {})".format(min_zoom, max_zoom)
        self.lblZoomRange.setText(zoom_range_text)

    def clip_tiles(self):
        return self.chkClipTiles.isChecked()

    def auto_zoom_enabled(self):
        return self.rbAutoZoom.isChecked()

    def manual_zoom(self):
        if not self.rbZoomManual.isChecked():
            return None
        return self.zoomSpin.value()

    def tile_number_limit(self):
        if not self.chkLimitNrOfTiles.isChecked():
            return None
        return self.spinNrOfLoadedTiles.value()

    def apply_styles_enabled(self):
        return self.chkApplyStyles.isChecked()

    def merge_tiles_enabled(self):
        return self.chkMergeTiles.isChecked()

    def load_mask_layer_enabled(self):
        return False


class ProgressDialog(QtGui.QDialog, Ui_DlgProgress):
    on_cancel = pyqtSignal()

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.lblMessage.setVisible(False)
        self.btnCancel.clicked.connect(self._on_cancel)
        self._is_loading = False
        _update_size(self)

    def _on_cancel(self):
        self.btnCancel.setText("Cancelling...")
        self.btnCancel.setEnabled(False)
        self.on_cancel.emit()

    def set_maximum(self, max):
        self.progressBar.setMaximum(max)

    def set_progress(self, value):
        self.progressBar.setValue(value)

    def is_cancelling(self):
        return self._cancelling

    def is_loading(self):
        return self._is_loading

    def set_message(self, msg=None):
        self.lblMessage.setText(msg)
        if msg:
            self.lblMessage.setVisible(True)
        else:
            self.lblMessage.setVisible(False)

    def open(self):
        self._is_loading = True
        self.show()

    def hide(self):
        self._is_loading = False
        self.close()


class ConnectionsDialog(QtGui.QDialog, Ui_DlgConnections):

    on_connect = pyqtSignal('QString', 'QString')
    on_add = pyqtSignal('QString', 'QString', list)
    on_connection_change = pyqtSignal()
    on_zoom_change = pyqtSignal()

    _connections_array = "connections"
    _table_headers = OrderedDict([
        ("ID", "id"),
        ("Min. Zoom", "minzoom"),
        ("Max. Zoom", "maxzoom"),
        ("Description", "description")
    ])

    _OMT = "OpenMapTiles.com"
    _MAPZEN = "Mapzen.com"

    _predefined_connections = {
        _OMT: "https://free.tilehosting.com/data/v3.json?key={token}",
        _MAPZEN: "http://tile.mapzen.com/mapzen/vector/v1/tilejson/mapbox.json?api_key={token}"
    }
    _tokens = {
        _OMT: "6irhAXGgsi8TrIDL0211",
        _MAPZEN: "mapzen-7SNUCXx"
    }

    def __init__(self, default_browse_directory):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.options = OptionsGroup(self.grpOptions, self._on_zoom_change)
        self.settings = QSettings("VtrSettings")
        self.connections = {}
        self.selected_connection = None
        self.selected_layer_id = None
        self.cbxConnections.currentIndexChanged['QString'].connect(self._handle_connection_change)
        self.btnCreateConnection.clicked.connect(self._create_connection)
        self.btnConnect.clicked.connect(self._handle_connect)
        self.btnEdit.clicked.connect(self._edit_connection)
        self.btnDelete.clicked.connect(self._delete_connection)
        self.btnAdd.clicked.connect(self._load_tiles_for_connection)
        self.btnSave.clicked.connect(self._export_connections)
        self.btnLoad.clicked.connect(self._import_connections)
        self.btnHelp.clicked.connect(lambda: webbrowser.open(_HELP_URL))
        self.btnBrowse.clicked.connect(self._select_file_path)
        self.btnBrowseTrexCache.clicked.connect(self._select_trex_cache_folder)
        self.open_path = None
        self.browse_path = default_browse_directory
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(self._table_headers.keys())
        self.tblLayers.setModel(self.model)
        self._load_connections()
        self._add_loaded_connections()
        self.edit_connection_dialog = EditConnectionDialog()
        _update_size(self)

    def _select_file_path(self):
        open_file_name = QFileDialog.getOpenFileName(None, "Select Mapbox Tiles", self.browse_path, "Mapbox Tiles (*.mbtiles)")
        if open_file_name and os.path.isfile(open_file_name):
            self.txtPath.setText(open_file_name)
            self._handle_path_or_folder_selection(open_file_name)

    def _select_trex_cache_folder(self):
        open_file_name = QFileDialog.getExistingDirectory(None, "Select t-rex Cache directory", self.browse_path)
        if open_file_name and os.path.isdir(open_file_name):
            self.txtTrexCachePath.setText(open_file_name)
            self._handle_path_or_folder_selection(open_file_name)

    def _handle_path_or_folder_selection(self, path):
        self.browse_path = path
        self.open_path = path
        name = os.path.basename(path)
        self.on_connect.emit(name, path)

    def _on_zoom_change(self):
        self.on_zoom_change.emit()

    def set_nr_of_tiles(self, nr_tiles):
        self.options.set_nr_of_tiles(nr_tiles)

    def _load_tiles_for_connection(self):
        indexes = self.tblLayers.selectionModel().selectedRows()
        selected_layers = map(lambda i: self.model.item(i.row()).text(), indexes)
        name, url = self._get_current_connection()
        self.on_add.emit(name, url, selected_layers)

    def _export_connections(self):
        file_name = QFileDialog.getSaveFileName(None, "Export Vector Tile Reader Connections", "", "csv (*.csv)")
        if file_name:
            with open(file_name, 'w') as csvfile:
                fieldnames = ['name', 'url']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for name in self.connections:
                    writer.writerow({'name': name, 'url': self.connections[name]})

    def _import_connections(self):
        file_name = QFileDialog.getOpenFileName(None, "Export Vector Tile Reader Connections", "", "csv (*.csv)")
        if file_name:
            with open(file_name, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    self._set_connection_url(row['name'], row['url'])
            self._add_loaded_connections()

    def _load_connections(self):
        settings = self.settings
        connections = settings.beginReadArray(self._connections_array)
        for i in range(connections):
            settings.setArrayIndex(i)
            name = settings.value("name")
            url = settings.value("url")
            self._set_connection_url(name, url)
        settings.endArray()

    def _add_loaded_connections(self):
        for index, name in enumerate(self._predefined_connections.keys()):
            url = self._predefined_connections[name]
            self._set_connection_url(name, url)

        for name in sorted(self.connections):
            is_already_added = self.cbxConnections.findText(name) != -1
            if not is_already_added:
                self.cbxConnections.addItem(name)
        if len(self.connections) > 0:
            self.cbxConnections.setCurrentIndex(0)

    def _delete_connection(self):
        index = self.cbxConnections.currentIndex()
        connection = self.cbxConnections.currentText()
        msg = "Are you sure you want to remove the connection '{}' and all associated settings?".format(connection)
        reply = QMessageBox.question(self.activateWindow(), 'Confirm Delete', msg, QMessageBox.Yes, QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.cbxConnections.removeItem(index)
            self.connections.pop(connection)
            self._save_connections()

    def _save_connections(self):
        settings = self.settings
        settings.beginWriteArray(self._connections_array)
        for index, key in enumerate(self.connections):
            settings.setArrayIndex(index)
            settings.setValue("name", key)
            settings.setValue("url", self.connections[key])
        settings.endArray()

    def _set_connection_url(self, name, url):
        self.connections[name] = url

    def _handle_connect(self):
        conn = self._get_current_connection()
        name = conn[0]
        url = conn[1]
        self.on_connect.emit(name, url)
        self.txtPath.setText("")

    def _get_current_connection(self):
        if self.tabServer.isEnabled():
            name = self.cbxConnections.currentText()
            url = self.connections[name]
        elif self.tabFile.isEnabled():
            url = self.txtPath.text()
            name = os.path.basename(url)
        else:
            url = self.txtTrexCachePath.text()
            name = os.path.basename(url)
        if name in self._predefined_connections:
            url = url.replace("{token}", self._tokens[name])
        return name, url

    def show(self):
        self.exec_()

    def keep_dialog_open(self):
        return self.chkKeepOpen.isChecked()

    def set_layers(self, layers):
        self.model.removeRows(0, self.model.rowCount())

        for row_index, layer in enumerate(sorted(layers)):
            for header_index, header in enumerate(self._table_headers.keys()):
                header_value = self._table_headers[header]
                if header_value in layer:
                    value = str(layer[header_value])
                else:
                    value = "-"
                self.model.setItem(row_index, header_index, QStandardItem(value))
        add_enabled = layers is not None and len(layers) > 0
        self.btnAdd.setEnabled(add_enabled)

    def _edit_connection(self):
        conn = self._get_current_connection()
        self._create_or_update_connection(name=conn[0], url=conn[1])

    def _create_connection(self):
        self._create_or_update_connection("", "")

    def _create_or_update_connection(self, name=None, url=None):
        self.edit_connection_dialog.set_name_and_path(name, url)
        result = self.edit_connection_dialog.exec_()
        if result == QtGui.QDialog.Accepted:
            newname, newurl = self.edit_connection_dialog.get_connection()
            self._set_connection_url(newname, newurl)
            if newname != name:
                self.cbxConnections.addItem(newname)
                self.cbxConnections.setCurrentIndex(len(self.connections)-1)
            self._save_connections()

    def _handle_connection_change(self, name):
        self.set_layers([])
        enable_connect = False
        enable_edit = False
        if name in self.connections:
            enable_connect = True
            enable_edit = name not in self._predefined_connections
            is_omt = name == "OpenMapTiles.com"
            self.options.set_omt_styles_enabled(is_omt)

        self.btnConnect.setEnabled(enable_connect)
        self.btnEdit.setEnabled(enable_edit)
        self.btnDelete.setEnabled(enable_edit)
        self.on_connection_change.emit()


class EditConnectionDialog(QtGui.QDialog, Ui_DlgEditConnection):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.txtName.textChanged.connect(self._update_save_btn_state)
        self.txtUrl.textChanged.connect(self._update_save_btn_state)
        _update_size(self)

    def set_name_and_path(self, name, path_or_url):
        if name is not None:
            self.txtName.setText(name)
        if path_or_url is not None:
            self.txtUrl.setText(path_or_url)

    @staticmethod
    def _is_url(path):
        return path.lower().startswith("http://") or path.lower().startswith("https://")

    def _select_file_path(self):
        open_file_name = QFileDialog.getOpenFileName(None, "Select Mapbox Tiles", self.browse_path, "Mapbox Tiles (*.mbtiles)")
        if open_file_name:
            if not self._is_url(open_file_name):
                self.browse_path = open_file_name
            self.open_path = open_file_name
            self.txtUrl.setText(open_file_name)

    def _update_save_btn_state(self):
        enable = False
        if self.txtName.text() and self.txtUrl.text():
            enable = True
        self.btnSave.setEnabled(enable)

    def get_connection(self):
        return self.txtName.text(), self.txtUrl.text()

