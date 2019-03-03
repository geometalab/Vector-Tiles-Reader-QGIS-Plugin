import copy
import webbrowser
import ast
from collections import OrderedDict
import os

from .options_group import OptionsGroup
from .connections_group import ConnectionsGroup

from .qt.dlg_about_qt5 import Ui_DlgAbout
from .qt.dlg_connections_qt5 import Ui_DlgConnections
from .qt.dlg_edit_postgis_connection_qt5 import Ui_DlgEditPostgisConnection
from .qt.dlg_edit_tilejson_connection_qt5 import Ui_DlgEditTileJSONConnection

from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, QSettings, pyqtBoundSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem

if "VTR_TESTS" not in os.environ or os.environ["VTR_TESTS"] != '1':
    from ..ui import resources_rc_qt5

from ..util.connection import (
    ConnectionTypes,
    MBTILES_CONNECTION_TEMPLATE,
    TILEJSON_CONNECTION_TEMPLATE,
    DIRECTORY_CONNECTION_TEMPLATE)

_HELP_URL = "https://github.com/geometalab/Vector-Tiles-Reader-QGIS-Plugin/wiki/Help"


def _update_size(dialog: QDialog):
    screen_resolution = QApplication.desktop().screenGeometry()
    screen_width, screen_height = screen_resolution.width(), screen_resolution.height()
    new_width = None
    new_height = None
    if screen_width > 1920 or screen_height > 1080:
        new_width = int(dialog.width() / 1920.0 * screen_width)
        new_height = int(dialog.height() / 1080.0 * screen_height)
        dialog.setMinimumSize(new_width, new_height)
    elif dialog.width() >= screen_width or dialog.height() >= screen_height:
        margin = 40
        new_width = screen_width - margin
        new_height = screen_height - margin

    if new_width and new_height:
        dialog.resize(new_width, new_height)


class AboutDialog(QDialog, Ui_DlgAbout):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
        self._load_about()
        _update_size(self)

    def _load_about(self) -> None:
        about_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "about.html")
        if os.path.isfile(about_path):
            with open(about_path, 'r') as f:
                html = f.read()
                self.txtAbout.setHtml(html)

    def show(self):
        self.exec_()


class ConnectionsDialog(QDialog, Ui_DlgConnections):

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

    _OMT = "OpenMapTiles.com (default entry with credits)"
    _OMT_CUSTOM_KEY = "OpenMapTiles.com (with custom key)"
    _MAPZEN = "Mapzen.com (default entry with credits)"
    _MAPCAT = "Mapcat.com (default entry with credits)"
    _NEXTZEN = "Nextzen.org (default entry with credits)"

    _predefined_tilejson_connections = {
        _OMT: {
            "name": _OMT,
            "url": "https://free.tilehosting.com/data/v3.json?key={token}",
            "token": "6irhAXGgsi8TrIDL0211",
            "style": "https://raw.githubusercontent.com/openmaptiles/osm-bright-gl-style/master/style.json"
        },
        _OMT_CUSTOM_KEY: {
            "name": _OMT_CUSTOM_KEY,
            "url": "https://maps.tilehosting.com/data/v3.json?key={token}",
            "can_edit": True,
            "style": "https://raw.githubusercontent.com/openmaptiles/osm-bright-gl-style/master/style.json"
        },
        _MAPZEN: {
            "disabled": True,
            "name": _MAPZEN,
            "url": "http://tile.mapzen.com/mapzen/vector/v1/tilejson/mapbox.json?api_key={token}",
            "token": "mapzen-7SNUCXx"
        },
        _MAPCAT: {
            "disabled": True,
            "name": _MAPCAT,
            "url": "https://api.mapcat.com/api/mapinit/tile?api_key={token}",
            "style": "https://api.mapcat.com/api/mapinit/vector?api_key={token}",
            "token": "VmKNOOCry7SE4c8FyacQ1KxojeWzY1W2aFS0TADq"
        },
        _NEXTZEN: {
            "name": _NEXTZEN,
            "url": "https://tile.nextzen.org/tilezen/vector/v1/512/all/tilejson.mvt.json?api_key={token}",
            "token": "80xAN5o0QuyFrcPVVIieTA"
        }
    }

    _CONNECTIONS_TAB = "selected_connections_tab"
    _CURRENT_ONLINE_CONNECTION = "current_online_connection"

    _qgis_zoom = None

    def __init__(self, default_browse_directory):
        QDialog.__init__(self)
        self.setupUi(self)
        self.action_text = "Add"
        self._nr_of_tiles = None
        self._current_connection_already_loaded = False
        self.settings = QSettings("VtrSettings")
        self.options = OptionsGroup(self.settings, self.grpOptions, self._on_zoom_change)
        last_tab = self.settings.value(self._CONNECTIONS_TAB, 0)
        self.tabConnections.setCurrentIndex(int(last_tab))
        self.tilejson_connections = ConnectionsGroup(target_groupbox=self.grpTilejsonConnections,
                                                     edit_dialog=EditTilejsonConnectionDialog(),
                                                     connection_template=TILEJSON_CONNECTION_TEMPLATE,
                                                     settings_key="connections",
                                                     settings=self.settings,
                                                     predefined_connections=self._predefined_tilejson_connections)
        connection_to_select = self.settings.value(self._CURRENT_ONLINE_CONNECTION, None)
        if not connection_to_select:
            connection_to_select = self._OMT
        self.tilejson_connections.select_connection(connection_to_select)
        self.btnConnectDirectory.clicked.connect(lambda: self.connect_to(self._directory_conn))
        self.btnConnectFile.clicked.connect(lambda: self.connect_to(self._mbtiles_conn))
        self.tabConnections.currentChanged.connect(self._handle_tab_change)
        self.tilejson_connections.on_connect.connect(self._handle_connect)
        self.tilejson_connections.on_connection_change.connect(self._handle_connection_change)
        self.selected_layer_id = None
        self.btnAdd.clicked.connect(self._load_tiles_for_connection)
        self.btnHelp.clicked.connect(lambda: webbrowser.open(_HELP_URL))
        self.btnBrowse.clicked.connect(self._select_file_path)
        self.btnSelectDirectory.clicked.connect(self._select_directory)
        self.open_path = None
        self.browse_path = default_browse_directory
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(self._table_headers.keys())
        self.tblLayers.setModel(self.model)
        _update_size(self)
        self._current_connection = None
        self._directory_conn = None
        self._mbtiles_conn = None
        self._load_mbtiles_and_directory_connections()

    def _update_action_text(self, connection):
        if connection and self._current_connection == connection and self._current_connection_already_loaded:
            action_text = "Reload"
        else:
            action_text = "Add"
        self.btnAdd.setText(action_text)
        self.setWindowTitle("{} Layer(s) from a Vector Tile Source".format(action_text))

    def _load_mbtiles_and_directory_connections(self):
        mbtiles_conn = self.settings.value("mbtiles_connection")
        directory_conn = self.settings.value("directory_connection")
        if mbtiles_conn:
            mbtiles_conn = ast.literal_eval(mbtiles_conn)
            if mbtiles_conn["type"] == ConnectionTypes.MBTiles:
                if mbtiles_conn["path"]:
                    self.txtPath.setText(mbtiles_conn["path"])
                if mbtiles_conn["style"]:
                    self.txtMbtilesStyleJsonUrl.setText(mbtiles_conn["style"])
        if directory_conn:
            directory_conn = ast.literal_eval(directory_conn)
            if directory_conn["type"] == ConnectionTypes.Directory:
                if directory_conn["path"]:
                    self.txtDirectoryPath.setText(directory_conn["path"])
                if directory_conn["style"]:
                    self.txtDirectoryStyleJsonUrl.setText(directory_conn["style"])
        self._mbtiles_conn = mbtiles_conn
        self._directory_conn = directory_conn

    def connect_to(self, connection):
        self._update_layers_group_title(connection)
        if connection:
            self._handle_connect(connection)
            widget = None
            if connection["type"] == ConnectionTypes.TileJSON:
                widget = self.tabServer
            elif connection["type"] == ConnectionTypes.MBTiles:
                widget = self.tabFile
            elif connection["type"] == ConnectionTypes.Directory:
                widget = self.tabDirectory
            if widget:
                self.tabConnections.setCurrentWidget(widget)

    def _update_layers_group_title(self, connection):
        if connection:
            layers_group_title = "Layers of '{}'".format(connection["name"])
            self.grpLayers.setTitle(layers_group_title)

    def _handle_tab_change(self, current_index):
        self.settings.setValue(self._CONNECTIONS_TAB, current_index)

    def _handle_connect(self, connection):
        self._update_layers_group_title(connection)
        if connection:
            self._current_connection = connection
            self.on_connect.emit(connection)

    def _handle_connection_change(self, name):
        self.settings.setValue(self._CURRENT_ONLINE_CONNECTION, name)
        self.set_layers([])
        conn = self.tilejson_connections.get_current_connection()
        has_style = "style" in conn and len(conn["style"]) > 0
        self.options.set_styles_enabled(has_style)
        self.on_connection_change.emit()

    def _select_file_path(self):
        open_file_name = QFileDialog.getOpenFileName(None, "Select Mapbox Tiles", self.browse_path, "Mapbox Tiles (*.mbtiles)")
        if isinstance(open_file_name, tuple):
            open_file_name = open_file_name[0]
        if open_file_name and os.path.isfile(open_file_name):
            self.txtPath.setText(open_file_name)
            connection = copy.deepcopy(MBTILES_CONNECTION_TEMPLATE)
            connection["name"] = os.path.basename(open_file_name)
            connection["path"] = open_file_name
            self._handle_path_or_folder_selection(connection)

    def _select_directory(self):
        open_file_name = QFileDialog.getExistingDirectory(None, "Select directory", self.browse_path)
        if isinstance(open_file_name, tuple):
            open_file_name = open_file_name[0]
        if open_file_name and os.path.isdir(open_file_name):
            self.txtDirectoryPath.setText(open_file_name)
            connection = copy.deepcopy(DIRECTORY_CONNECTION_TEMPLATE)
            connection["name"] = os.path.basename(open_file_name)
            connection["path"] = open_file_name
            self._handle_path_or_folder_selection(connection)

    def _handle_path_or_folder_selection(self, connection):
        self._current_connection = connection
        path = connection["path"]
        self.browse_path = path
        self.open_path = path
        self.on_directory_change.emit(os.path.dirname(path))
        self.on_connect.emit(connection)

    def _on_zoom_change(self):
        self.on_zoom_change.emit()

    def set_current_zoom_level(self, zoom_level, set_immediately=True):
        """
         Sets the zoom level in the spinner for the manual zoom selection.
        :param zoom_level:
        :param set_immediately: If true, the value will directly be set in the spinner, otherwise it'll be assigned
            to a variable and only be set, if the "Analysis defaults" button is clicked.
        :return:
        """
        self.options.set_zoom_level(zoom_level, set_immediately=set_immediately)

    def set_nr_of_tiles(self, nr_tiles):
        """
        Sets the number of expected tiles to be loaded
        :param nr_tiles:
        :return:
        """
        self.options.set_nr_of_tiles(nr_tiles)
        self._nr_of_tiles = nr_tiles

    def _load_tiles_for_connection(self):
        indexes = self.tblLayers.selectionModel().selectedRows()
        selected_layers = list(map(lambda i: self.model.item(i.row()).text(), indexes))
        active_tab = self.tabConnections.currentWidget()
        if active_tab == self.tabFile and self._current_connection["type"] == ConnectionTypes.MBTiles:
            self._current_connection["style"] = self.txtMbtilesStyleJsonUrl.text()
            self.settings.setValue("mbtiles_connection", str(self._current_connection))
        elif active_tab == self.tabDirectory and self._current_connection["type"] == ConnectionTypes.Directory:
            self._current_connection["style"] = self.txtDirectoryStyleJsonUrl.text()
            self.settings.setValue("directory_connection", str(self._current_connection))

        load = True
        threshold = 20
        if self._nr_of_tiles > threshold and not self.options.tile_number_limit():
            msg = "You are about to load {} tiles. That's a lot and may take some while. Do you want to continue?"\
                .format(self._nr_of_tiles)
            reply = QMessageBox.question(self.activateWindow(), 'Confirm Load', msg, QMessageBox.Yes, QMessageBox.No)
            if reply != QMessageBox.Yes:
                load = False
        if load:
            self.on_add.emit(self._current_connection, selected_layers)

    def set_current_connection_already_loaded(self, is_loaded: bool):
        self._current_connection_already_loaded = is_loaded
        self._update_action_text(self._current_connection)

    def display(self, current_connection):
        self._update_action_text(current_connection)
        active_tab = self.tabConnections.currentWidget()
        if active_tab == self.tabFile and self._mbtiles_conn and current_connection != self._mbtiles_conn:
            self.connect_to(self._mbtiles_conn)
        elif active_tab == self.tabDirectory and self._directory_conn and current_connection != self._mbtiles_conn:
            self.connect_to(self._directory_conn)
        self.on_zoom_change.emit()
        self.exec_()

    def keep_dialog_open(self):
        return self.chkKeepOpen.isChecked()

    def set_layers(self, layers):
        self.model.removeRows(0, self.model.rowCount())
        for row_index, layer in enumerate(layers):
            for header_index, header in enumerate(self._table_headers.keys()):
                header_value = self._table_headers[header]
                if header_value in layer:
                    value = str(layer[header_value])
                else:
                    value = "-"
                self.model.setItem(row_index, header_index, QStandardItem(value))
        self.model.sort(0)
        add_enabled = layers is not None and len(layers) > 0
        self.btnAdd.setEnabled(add_enabled)


class EditPostgisConnectionDialog(QDialog, Ui_DlgEditPostgisConnection):

    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
        _update_size(self)
        self._connection = None

    def set_mode(self, edit_mode):
        if edit_mode:
            self.setWindowTitle("Edit Connection")
        else:
            self.setWindowTitle("Create Connection")

    def set_connection(self, connection):
        self._connection = copy.deepcopy(connection)
        self.txtpgName.setText(self._connection["name"])
        self.txtpgHost.setText(self._connection["host"])
        self.spinpgPort.setValue(self._connection["port"])
        self.txtpgUsername.setText(self._connection["username"])
        self.txtpgPassword.setText(self._connection["password"])
        self.txtpgDatabase.setText(self._connection["database"])
        if self._connection["save_password"]:
            self.chkpgStorePassword.setChecked(True)
        else:
            self.chkpgStorePassword.setChecked(False)

    def get_connection(self):
        self._connection["name"] = self.txtpgName.text()
        self._connection["host"] = self.txtpgHost.text()
        self._connection["username"] = self.txtpgUsername.text()
        self._connection["password"] = self.txtpgPassword.text()
        self._connection["port"] = self.spinpgPort.value()
        self._connection["database"] = self.txtpgDatabase.text()
        self._connection["save_password"] = self.chkpgStorePassword.isChecked()
        return self._connection


class EditTilejsonConnectionDialog(QDialog, Ui_DlgEditTileJSONConnection):

    def __init__(self):
        QDialog.__init__(self)
        self.setupUi(self)
        self.txtName.textChanged.connect(self._update_save_btn_state)
        self.txtUrl.textChanged.connect(self._update_save_btn_state)
        self._connection = None
        _update_size(self)

    def set_mode(self, edit_mode):
        if edit_mode:
            self.setWindowTitle("Edit Connection")
        else:
            self.setWindowTitle("Create Connection")

    def set_connection(self, connection):
        self._connection = copy.deepcopy(connection)
        name = connection["name"]
        url = connection["url"]
        if name is not None:
            self.txtName.setText(name)
        if url is not None:
            self.txtUrl.setText(url)
        if connection["style"] is not None:
            self.txtStyleJsonUrl.setText(connection["style"])

    @staticmethod
    def _is_url(path):
        return path.lower().startswith("http://") or path.lower().startswith("https://")

    def _select_file_path(self):
        open_file_name = QFileDialog.getOpenFileName(None,
                                                     caption="Select Mapbox Tiles",
                                                     directory=self.browse_path,
                                                     filter="Mapbox Tiles (*.mbtiles)")
        if isinstance(open_file_name, tuple):
            open_file_name = open_file_name[0]
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
        self._connection["name"] = self.txtName.text()
        self._connection["url"] = self.txtUrl.text()
        self._connection["style"] = self.txtStyleJsonUrl.text()
        return self._connection
