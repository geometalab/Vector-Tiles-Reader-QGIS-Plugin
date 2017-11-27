import copy
import csv
import webbrowser
import ast
from collections import OrderedDict

from ..util.vtr_2to3 import *
from ..util.log_helper import info

try:
    from .connections_group_qt5 import Ui_ConnectionsGroup
    from .dlg_about_qt5 import Ui_DlgAbout
    from .dlg_connections_qt5 import Ui_DlgConnections
    from .dlg_edit_postgis_connection_qt5 import Ui_DlgEditPostgisConnection
    from .dlg_edit_tilejson_connection_qt5 import Ui_DlgEditTileJSONConnection
    from .options_qt5 import Ui_OptionsGroup
except:
    from .connections_group_qt4 import Ui_ConnectionsGroup
    from .dlg_about_qt4 import Ui_DlgAbout
    from .dlg_connections_qt4 import Ui_DlgConnections
    from .dlg_edit_postgis_connection_qt4 import Ui_DlgEditPostgisConnection
    from .dlg_edit_tilejson_connection_qt4 import Ui_DlgEditTileJSONConnection
    from .options_qt4 import Ui_OptionsGroup


from ..util.connection import (
    ConnectionTypes,
    MBTILES_CONNECTION_TEMPLATE,
    TILEJSON_CONNECTION_TEMPLATE,
    DIRECTORY_CONNECTION_TEMPLATE)

_HELP_URL = "https://giswiki.hsr.ch/Vector_Tiles_Reader_QGIS_Plugin"


def _update_size(dialog):
    screen_resolution = QApplication.desktop().screenGeometry()
    screen_width, screen_height = screen_resolution.width(), screen_resolution.height()
    new_width = None
    new_height = None
    if screen_width > 1920 or screen_height > 1080:
        new_width = dialog.width() / 1920.0 * screen_width
        new_height = dialog.height() / 1080.0 * screen_height
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

    def _load_about(self):
        about_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "about.html")
        if os.path.isfile(about_path):
            with open(about_path, 'r') as f:
                html = f.read()
                self.txtAbout.setHtml(html)

    def show(self):
        self.exec_()


class ConnectionsGroup(QGroupBox, Ui_ConnectionsGroup):

    on_connect = pyqtSignal(dict)
    on_connection_change = pyqtSignal('QString')

    def __init__(self, target_groupbox, edit_dialog, connection_template, settings_key, settings, predefined_connections=None):
        super(QGroupBox, self).__init__()

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

    def select_connection(self, name):
        if name:
            index = self.cbxConnections.findText(name)
            if index:
                self.cbxConnections.setCurrentIndex(index)

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
                    connection = self.connections[name]
                    if connection["name"] and len(connection["name"]) > 0:
                        if connection["type"] == ConnectionTypes.PostGIS and not connection["save_password"]:
                            connection["password"] = None
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
                    name = new_connection["name"]
                    if name and len(name) > 0:
                        self.connections[name] = new_connection
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
            if new_connection["name"]:
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
        if reply == QMessageBox.Yes:
            self.cbxConnections.removeItem(index)
            self.connections.pop(connection)
            self._save_connections()

    def _save_connections(self):
        settings = self._settings
        settings.beginWriteArray(self._settings_key)
        for index, connection_name in enumerate(self.connections):
            connection = self.connections[connection_name]
            if connection["type"] == ConnectionTypes.PostGIS and not connection["save_password"]:
                connection["password"] = None
            settings.setArrayIndex(index)
            for key in self._connection_template:
                settings.setValue(key, connection[key])
        settings.endArray()

    def _edit_connection(self):
        conn = self._get_current_connection()
        self._create_or_update_connection(conn, edit_mode=True)

    def _create_connection(self):
        self._create_or_update_connection(copy.deepcopy(self._connection_template), edit_mode=False)

    def _create_or_update_connection(self, connection, edit_mode):
        name = connection["name"]
        self.edit_connection_dialog.set_connection(connection)
        self.edit_connection_dialog.set_mode(edit_mode=edit_mode)
        result = self.edit_connection_dialog.exec_()
        if result == QDialog.Accepted:
            new_connection = self.edit_connection_dialog.get_connection()
            new_name = new_connection["name"]
            self.connections[new_name] = new_connection
            if new_name != name:
                self.cbxConnections.addItem(new_name)
                if edit_mode:
                    self.cbxConnections.removeItem(self.cbxConnections.findText(name))
                self.cbxConnections.setCurrentIndex(self.cbxConnections.findText(new_name))
            self._save_connections()

    def _handle_connection_change(self, name):
        enable_connect = False
        enable_edit = False
        is_predefined_connection = False
        if name in self.connections:
            enable_connect = True
            can_edit = False
            is_predefined_connection = name in self._predefined_connections
            if is_predefined_connection:
                predefined_connection = self._predefined_connections[name]
                can_edit = "can_edit" in predefined_connection and predefined_connection["can_edit"]
            enable_edit = not is_predefined_connection or can_edit is not None and (can_edit == "true" or can_edit == True)
        self.btnConnect.setEnabled(enable_connect)
        self.btnEdit.setEnabled(enable_edit)
        self.btnDelete.setEnabled(not is_predefined_connection)
        self.on_connection_change.emit(name)

    def _get_current_connection(self):
        """
        * Returns the currently selected connection.
        * The {token} in the URL is replaced, so that the URL can be used.
        :return:
        """
        name = self.cbxConnections.currentText()
        connection = copy.deepcopy(self.connections[name])
        if self._predefined_connections and name in self._predefined_connections and connection["token"]:
            connection["url"] = connection["url"].replace("{token}", connection["token"])
        return connection


class OptionsGroup(QGroupBox, Ui_OptionsGroup):

    on_zoom_change = pyqtSignal()

    _TILE_LIMIT_ENABLED = "tile_limit_enabled"
    _TILE_LIMIT = "tile_limit"
    _MERGE_TILES = "merge_tiles"
    _CLIP_TILES = "clip_tiles"
    _AUTO_ZOOM = "auto_zoom"
    _MAX_ZOOM = "max_zoom"
    _FIX_ZOOM_ENABLED = "fix_zoom_enabled"
    _FIX_ZOOM = "fix_zoom"
    _APPLY_STYLES = "apply_styles"
    _SET_BACKGROUND_COLOR = "set_background_color"

    _options = {
        _TILE_LIMIT_ENABLED: True,
        _TILE_LIMIT: 32,
        _MERGE_TILES: False,
        _CLIP_TILES: False,
        _AUTO_ZOOM: True,
        _MAX_ZOOM: False,
        _FIX_ZOOM: 0,
        _FIX_ZOOM_ENABLED: False,
        _APPLY_STYLES: True,
        _SET_BACKGROUND_COLOR: True
    }

    def __init__(self, settings, target_groupbox, zoom_change_handler):
        super(QGroupBox, self).__init__()
        self.setupUi(target_groupbox)
        self._reset_to_basemap_defaults()
        self.settings = settings
        self._zoom_change_handler = zoom_change_handler
        self.lblZoomRange.setText("")
        self.chkLimitNrOfTiles.toggled.connect(lambda enabled: self.spinNrOfLoadedTiles.setEnabled(enabled))
        self.chkMergeTiles.toggled.connect(lambda enabled: self._set_option(self._MERGE_TILES, enabled))
        self.chkClipTiles.toggled.connect(lambda enabled: self._set_option(self._CLIP_TILES, enabled))
        self.chkSetBackgroundColor.toggled.connect(lambda enabled: self._set_option(self._SET_BACKGROUND_COLOR, enabled))
        self.chkApplyStyles.toggled.connect(self._on_apply_styles_changed)
        self.chkLimitNrOfTiles.toggled.connect(lambda enabled: self._set_option(self._TILE_LIMIT_ENABLED, enabled))
        self.rbZoomManual.toggled.connect(self._on_manual_zoom_enabled)
        self.rbZoomMax.toggled.connect(self._on_max_zoom_selected)
        self.rbAutoZoom.toggled.connect(self._zoom_change_handler)
        self.btnResetToBasemapDefaults.clicked.connect(self._reset_to_basemap_defaults)
        self.btnResetToInspectionDefaults.clicked.connect(self._reset_to_inspection_defaults)
        self.btnResetToAnalysisDefaults.clicked.connect(self._reset_to_analysis_defaults)
        self._load_options()
        self.spinNrOfLoadedTiles.valueChanged.connect(lambda v: self._set_option(self._TILE_LIMIT, v))
        self.zoomSpin.valueChanged.connect(self._on_manual_zoom_change)

    def _load_options(self):
        opt = self._options
        for key in self._options:
            self._options[key] = self.settings.value("options/{}".format(key), None)
        if opt[self._TILE_LIMIT_ENABLED]:
            self.chkLimitNrOfTiles.setChecked(opt[self._TILE_LIMIT_ENABLED] == True or opt[self._TILE_LIMIT_ENABLED] == "true")
        if opt[self._TILE_LIMIT]:
            self.spinNrOfLoadedTiles.setValue(int(opt[self._TILE_LIMIT]))
        if opt[self._MERGE_TILES]:
            self.chkMergeTiles.setChecked(opt[self._MERGE_TILES] == True or opt[self._MERGE_TILES] == "true")
        if opt[self._CLIP_TILES]:
            self.chkClipTiles.setChecked(opt[self._CLIP_TILES] == True or opt[self._CLIP_TILES] == "true")
        if opt[self._AUTO_ZOOM]:
            self.rbAutoZoom.setChecked(opt[self._AUTO_ZOOM] == True or opt[self._AUTO_ZOOM] == "true")
        if opt[self._MAX_ZOOM]:
            self.rbZoomMax.setChecked(opt[self._MAX_ZOOM] == True or opt[self._MAX_ZOOM] == "true")
        if opt[self._FIX_ZOOM]:
            self.zoomSpin.setValue(int(opt[self._FIX_ZOOM]))
        if opt[self._FIX_ZOOM_ENABLED]:
            self.rbZoomManual.setChecked(opt[self._FIX_ZOOM_ENABLED] == True or opt[self._FIX_ZOOM_ENABLED] == "true")
        if opt[self._APPLY_STYLES]:
            self.chkApplyStyles.setChecked(opt[self._APPLY_STYLES] == True or opt[self._APPLY_STYLES] == "true")
        if opt[self._SET_BACKGROUND_COLOR]:
            val = opt[self._SET_BACKGROUND_COLOR]
            self.chkSetBackgroundColor.setChecked(val == True or val == "true")

    def _on_apply_styles_changed(self, enabled):
        self._set_option(self._APPLY_STYLES, enabled)
        self.chkSetBackgroundColor.setEnabled(enabled)

    def _set_option(self, key, value):
        self._options[key] = value
        self.settings.setValue("options/{}".format(key), value)

    def _on_manual_zoom_enabled(self, enabled):
        self._set_option(self._FIX_ZOOM_ENABLED, enabled)
        self.zoomSpin.setEnabled(enabled)
        self._on_manual_zoom_change()

    def _on_manual_zoom_change(self):
        zoom = self.zoomSpin.value()
        self._set_option(self._FIX_ZOOM, zoom)
        self._zoom_change_handler()

    def _on_max_zoom_selected(self, enabled):
        self._set_option(self._MAX_ZOOM, enabled)
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
        self._set_option(self._APPLY_STYLES, enabled)
        self.chkApplyStyles.setChecked(enabled)

    def set_zoom(self, min_zoom=None, max_zoom=None):
        if min_zoom is not None:
            self.zoomSpin.setMinimum(min_zoom)
        else:
            self.zoomSpin.setMinimum(0)
        max_zoom_text = "Max. Zoom"
        if max_zoom is not None:
            self.zoomSpin.setMaximum(max_zoom)
            max_zoom_text += " ({})".format(max_zoom)
        else:
            self.zoomSpin.setMaximum(23)
        self.rbZoomMax.setText(max_zoom_text)

        zoom_range_text = ""
        if min_zoom is not None or max_zoom is not None:
            zoom_range_text = "({} - {})".format(min_zoom, max_zoom)
        self.lblZoomRange.setText(zoom_range_text)

    def clip_tiles(self):
        enabled = self.chkClipTiles.isChecked()
        self._set_option(self._CLIP_TILES, enabled)
        return enabled

    def auto_zoom_enabled(self):
        enabled = self.rbAutoZoom.isChecked()
        self._set_option(self._AUTO_ZOOM, enabled)
        return enabled

    def manual_zoom(self):
        enabled = self.rbZoomManual.isChecked()
        fix_zoom = self.zoomSpin.value()
        self._set_option(self._FIX_ZOOM_ENABLED, enabled)
        self._set_option(self._FIX_ZOOM, fix_zoom)
        if not enabled:
            return None
        return fix_zoom

    def tile_number_limit(self):
        enabled = self.chkLimitNrOfTiles.isChecked()
        tile_limit = self.spinNrOfLoadedTiles.value()
        self._set_option(self._TILE_LIMIT_ENABLED, enabled)
        self._set_option(self._TILE_LIMIT, tile_limit)
        if not enabled:
            return None
        return tile_limit

    def apply_styles_enabled(self):
        enabled = self.chkApplyStyles.isChecked()
        self._set_option(self._APPLY_STYLES, enabled)
        return enabled

    def set_background_color_enabled(self):
        return self.chkSetBackgroundColor.isChecked()

    def merge_tiles_enabled(self):
        enabled = self.chkMergeTiles.isChecked()
        self._set_option(self._MERGE_TILES, enabled)
        return enabled

    def load_mask_layer_enabled(self):
        return False


class ConnectionsDialog(QDialog, Ui_DlgConnections):

    on_connect = pyqtSignal(dict)
    on_connection_change = pyqtSignal()
    on_add = pyqtSignal(dict, dict)
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

    _predefined_tilejson_connections = {
        _OMT: {
            "name": _OMT,
            "url": "https://free.tilehosting.com/data/v3.json?key={token}",
            "token": "6irhAXGgsi8TrIDL0211",
            "style": "https://raw.githubusercontent.com/openmaptiles/klokantech-terrain-gl-style/master/style.json"
        },
        _OMT_CUSTOM_KEY: {
            "name": _OMT_CUSTOM_KEY,
            "url": "https://free.tilehosting.com/data/v3.json?key={api_key}",
            "can_edit": True,
            "style": "https://raw.githubusercontent.com/openmaptiles/klokantech-terrain-gl-style/master/style.json"
        },
        _MAPZEN: {
            "name": _MAPZEN,
            "url": "http://tile.mapzen.com/mapzen/vector/v1/tilejson/mapbox.json?api_key={token}",
            "token": "mapzen-7SNUCXx"
        }
    }

    _CONNECTIONS_TAB = "selected_connections_tab"
    _CURRENT_ONLINE_CONNECTION = "current_online_connection"

    def __init__(self, default_browse_directory):
        QDialog.__init__(self)
        self.setupUi(self)
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
        self.btnConnectDirectory.clicked.connect(lambda: self.connect(self._directory_conn))
        self.btnConnectFile.clicked.connect(lambda: self.connect(self._mbtiles_conn))
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

    def _load_mbtiles_and_directory_connections(self):
        mbtiles_connn = self.settings.value("mbtiles_connection")
        directory_conn = self.settings.value("directory_connection")
        if mbtiles_connn:
            mbtiles_connn = ast.literal_eval(mbtiles_connn)
            self.txtPath.setText(mbtiles_connn["path"])
            self.txtMbtilesStyleJsonUrl.setText(mbtiles_connn["style"])
        if directory_conn:
            directory_conn = ast.literal_eval(directory_conn)
            self.txtDirectoryPath.setText(directory_conn["path"])
            self.txtDirectoryStyleJsonUrl.setText(directory_conn["style"])
        self._mbtiles_conn = mbtiles_connn
        self._directory_conn = directory_conn

    def connect(self, connection):
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
        is_omt = name.startswith("OpenMapTiles.com")
        self.options.set_omt_styles_enabled(is_omt)
        self.on_connection_change.emit()

    def _select_file_path(self):
        open_file_name = QFileDialog.getOpenFileName(None, "Select Mapbox Tiles", self.browse_path, "Mapbox Tiles (*.mbtiles)")
        if open_file_name and os.path.isfile(open_file_name):
            self.txtPath.setText(open_file_name)
            connection = copy.deepcopy(MBTILES_CONNECTION_TEMPLATE)
            connection["name"] = os.path.basename(open_file_name)
            connection["path"] = open_file_name
            self._handle_path_or_folder_selection(connection)

    def _select_directory(self):
        open_file_name = QFileDialog.getExistingDirectory(None, "Select directory", self.browse_path)
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

    def set_current_zoom_level(self, zoom_level):
        self.options.set_zoom_level(zoom_level)

    def set_nr_of_tiles(self, nr_tiles):
        self.options.set_nr_of_tiles(nr_tiles)

    def _load_tiles_for_connection(self):
        indexes = self.tblLayers.selectionModel().selectedRows()
        selected_layers = dict(map(lambda i: self.model.item(i.row()).text(), indexes))
        active_tab = self.tabConnections.currentWidget()
        if active_tab == self.tabFile:
            self._current_connection["style"] = self.txtMbtilesStyleJsonUrl.text()
            self.settings.setValue("mbtiles_connection", str(self._current_connection))
        elif active_tab == self.tabDirectory:
            self._current_connection["style"] = self.txtDirectoryStyleJsonUrl.text()
            self.settings.setValue("directory_connection", str(self._current_connection))
        self.on_add.emit(self._current_connection, selected_layers)

    def show(self, current_connection):
        active_tab = self.tabConnections.currentWidget()
        if active_tab == self.tabFile and self._mbtiles_conn and current_connection != self._mbtiles_conn:
            self.connect(self._mbtiles_conn)
        elif active_tab == self.tabDirectory and self._directory_conn and current_connection != self._mbtiles_conn:
            self.connect(self._directory_conn)
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
        self._connection["name"] = self.txtName.text()
        self._connection["url"] = self.txtUrl.text()
        return self._connection

