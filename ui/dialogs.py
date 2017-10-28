import os
import copy
import webbrowser
import csv
import resources_rc  # don't remove this import, otherwise the icons won't be working

from collections import OrderedDict
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal, QSettings
from PyQt4.QtGui import QFileDialog, QMessageBox, QStandardItemModel, QStandardItem, QApplication
from dlg_connections import Ui_DlgConnections
from dlg_edit_tilejson_connection import Ui_DlgEditTileJSONConnection
from dlg_edit_postgis_connection import Ui_DlgEditPostgisConnection
from dlg_about import Ui_DlgAbout
from options import Ui_OptionsGroup
from connections_group import Ui_ConnectionsGroup
from ..log_helper import *
from ..connection import ConnectionTypes


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


class ConnectionsGroup(QtGui.QGroupBox, Ui_ConnectionsGroup):

    on_connect = pyqtSignal(dict)
    on_connection_change = pyqtSignal('QString')

    def __init__(self, target_groupbox, edit_dialog, connection_template, settings_key, settings, predefined_connections=None):
        super(QtGui.QGroupBox, self).__init__()

        self._connection_template = connection_template
        cloned_predefined_connections = {}
        if predefined_connections:
            for name in predefined_connections:
                predefined_connection = predefined_connections[name]
                clone = self._apply_template_connection(predefined_connection)
                cloned_predefined_connections[name] = clone

        self.setupUi(target_groupbox)
        self._settings = settings
        self._settings_key = settings_key
        self._predefined_connections = cloned_predefined_connections
        self.btnConnect.clicked.connect(self._handle_connect)
        self.btnEdit.clicked.connect(self._edit_connection)
        self.btnDelete.clicked.connect(self._delete_connection)
        self.btnSave.clicked.connect(self._export_connections)
        self.btnLoad.clicked.connect(self._import_connections)
        self.cbxConnections.currentIndexChanged['QString'].connect(self._handle_connection_change)
        self.btnCreateConnection.clicked.connect(self._create_connection)
        self.connections = {}
        self.selected_connection = None
        self._load_connections()
        self._add_loaded_connections_to_combobox()
        self.edit_connection_dialog = edit_dialog

    def _apply_template_connection(self, connection):
        clone = copy.deepcopy(self._connection_template)
        for key in clone:
            if key in connection and connection[key]:
                clone[key] = connection[key]
        return clone

    def _handle_connect(self):
        conn = self._get_current_connection()
        self.on_connect.emit(conn)

    def _export_connections(self):
        file_name = QFileDialog.getSaveFileName(None, "Export Vector Tile Reader Connections", "", "csv (*.csv)")
        if file_name:
            with open(file_name, 'w') as csvfile:
                fieldnames = self._connection_template.keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for name in self.connections:
                    writer.writerow(self.connections[name])

    def _import_connections(self):
        file_name = QFileDialog.getOpenFileName(None, "Export Vector Tile Reader Connections", "", "csv (*.csv)")
        if file_name:
            with open(file_name, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    new_connection = copy.deepcopy(self._connection_template)
                    for key in new_connection:
                        new_connection[key] = row[key]
                    self.connections[new_connection["name"]] = new_connection
            self._add_loaded_connections_to_combobox()

    def _load_connections(self):
        settings = self._settings
        connections = settings.beginReadArray(self._settings_key)
        for i in range(connections):
            settings.setArrayIndex(i)
            new_connection = self._apply_template_connection({})
            for key in new_connection:
                val = settings.value(key)
                if val:
                    new_connection[key] = val
            self.connections[new_connection["name"]] = new_connection
        settings.endArray()

    def _add_loaded_connections_to_combobox(self):
        if self._predefined_connections:
            for index, name in enumerate(self._predefined_connections):
                self.connections[name] = self._predefined_connections[name]

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
        settings = self._settings
        settings.beginWriteArray(self._settings_key)
        for index, connection_name in enumerate(self.connections):
            connection = self.connections[connection_name]
            settings.setArrayIndex(index)
            for key in self._connection_template:
                settings.setValue(key, connection[key])
        settings.endArray()

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
        enable_connect = False
        enable_edit = False
        if name in self.connections:
            enable_connect = True
            enable_edit = self._predefined_connections is None or name not in self._predefined_connections

        self.btnConnect.setEnabled(enable_connect)
        self.btnEdit.setEnabled(enable_edit)
        self.btnDelete.setEnabled(enable_edit)
        self.on_connection_change.emit(name)

    def _get_current_connection(self):
        name = self.cbxConnections.currentText()
        connection = copy.deepcopy(self.connections[name])

        if self._predefined_connections and name in self._predefined_connections:
            connection["url"] = connection["url"].replace("{token}", connection["token"])
        return connection


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

    def set_zoom_level(self, zoom_level):
        self.zoomSpin.setValue(zoom_level)

    def set_nr_of_tiles(self, nr_tiles):
        self.lblNumberTilesInCurrentExtent.setText("(Current extent: {} tiles)".format(nr_tiles))

    def _reset_to_basemap_defaults(self):
        self._set_settings(auto_zoom=True, fix_zoom=False, tile_limit=32, styles_enabled=True, merging_enabled=False,
                           clip_tile_at_bounds=False)

    def _reset_to_analysis_defaults(self):
        self._set_settings(auto_zoom=False, fix_zoom=True, tile_limit=10, styles_enabled=False, merging_enabled=True,
                           clip_tile_at_bounds=True)

    def _reset_to_inspection_defaults(self):
        self._set_settings(auto_zoom=False, fix_zoom=False, tile_limit=1, styles_enabled=False, merging_enabled=False,
                           clip_tile_at_bounds=False)

    def _set_settings(self, auto_zoom, fix_zoom, tile_limit, styles_enabled, merging_enabled, clip_tile_at_bounds):
        self.rbZoomMax.setChecked(not auto_zoom and not fix_zoom)
        self.rbAutoZoom.setChecked(auto_zoom)
        self.rbZoomManual.setChecked(fix_zoom)
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


class ConnectionsDialog(QtGui.QDialog, Ui_DlgConnections):

    on_connect = pyqtSignal(dict)
    on_connection_change = pyqtSignal()
    on_add = pyqtSignal(dict, list)
    on_zoom_change = pyqtSignal()
    on_directory_change = pyqtSignal("QString")

    _table_headers = OrderedDict([
        ("ID", "id"),
        ("Min. Zoom", "minzoom"),
        ("Max. Zoom", "maxzoom"),
        ("Description", "description")
    ])

    _TILEJSON_CONNECTION_TEMPLATE = {
        "name": None,
        "url": None,
        "token": None,
        "type": ConnectionTypes.TileJSON
    }

    _POSTGIS_CONNECTION_TEMPLATE = {
        "name": None,
        "host": None,
        "port": 5432,
        "username": "postgres",
        "password": None,
        "database": None,
        "type": ConnectionTypes.PostGIS
    }

    _OMT = "OpenMapTiles.com (default entry with credits)"
    _MAPZEN = "Mapzen.com (default entry with credits)"

    _predefined_tilejson_connections = {
        _OMT: {
            "name": _OMT,
            "url": "https://free.tilehosting.com/data/v3.json?key={token}",
            "token": "6irhAXGgsi8TrIDL0211"
        },
        _MAPZEN: {
            "name": _MAPZEN,
            "url": "http://tile.mapzen.com/mapzen/vector/v1/tilejson/mapbox.json?api_key={token}",
            "token": "mapzen-7SNUCXx"
        }
    }

    def __init__(self, default_browse_directory):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.options = OptionsGroup(self.grpOptions, self._on_zoom_change)
        settings = QSettings("VtrSettings")
        self.tilejson_connections = ConnectionsGroup(target_groupbox=self.grpTilejsonConnections,
                                                     edit_dialog=EditTilejsonConnectionDialog(),
                                                     connection_template=self._TILEJSON_CONNECTION_TEMPLATE,
                                                     settings_key="connections",
                                                     settings=settings,
                                                     predefined_connections=self._predefined_tilejson_connections)
        self.postgis_connections = ConnectionsGroup(target_groupbox=self.grpPostgisConnections,
                                                    edit_dialog=Ui_DlgEditPostgisConnection(),
                                                    connection_template=self._POSTGIS_CONNECTION_TEMPLATE,
                                                    settings_key="PostGISConnections",
                                                    settings=settings)

        self.tilejson_connections.on_connect.connect(self._handle_connect)
        self.tilejson_connections.on_connection_change.connect(self._handle_connection_change)
        self.postgis_connections.on_connect.connect(self._handle_connect)
        self.postgis_connections.on_connection_change.connect(self._handle_connection_change)

        self.selected_layer_id = None

        self.btnAdd.clicked.connect(self._load_tiles_for_connection)
        self.btnHelp.clicked.connect(lambda: webbrowser.open(_HELP_URL))
        self.btnBrowse.clicked.connect(self._select_file_path)
        self.btnBrowseTrexCache.clicked.connect(self._select_trex_cache_folder)
        self.open_path = None
        self.browse_path = default_browse_directory
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(self._table_headers.keys())
        self.tblLayers.setModel(self.model)
        _update_size(self)

    def _handle_connect(self, connection):
        self._current_connection = connection
        self.on_connect.emit(connection)
        active_tab = self.tabConnections.currentWidget()
        if active_tab != self.tabFile:
            self.txtPath.setText("")

    def _handle_connection_change(self, name):
        self.set_layers([])
        is_omt = name.startswith("OpenMapTiles.com")
        self.options.set_omt_styles_enabled(is_omt)
        self.on_connection_change.emit()

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
        self.on_directory_change.emit(os.path.dirname(path))
        self.on_connect.emit(name, path)

    def _on_zoom_change(self):
        self.on_zoom_change.emit()

    def set_current_zoom_level(self, zoom_level):
        self.options.set_zoom_level(zoom_level)

    def set_nr_of_tiles(self, nr_tiles):
        self.options.set_nr_of_tiles(nr_tiles)

    def _load_tiles_for_connection(self):
        indexes = self.tblLayers.selectionModel().selectedRows()
        selected_layers = map(lambda i: self.model.item(i.row()).text(), indexes)
        self.on_add.emit(self._current_connection, selected_layers)

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


class EditPostgisConnectionDialog(QtGui.QDialog, Ui_DlgEditPostgisConnection):

    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        _update_size(self)


class EditTilejsonConnectionDialog(QtGui.QDialog, Ui_DlgEditTileJSONConnection):

    new_connection_template = {
        "name": None,
        "url": None
    }

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

