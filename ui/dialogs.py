import os
import webbrowser
import csv

from collections import OrderedDict
from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal, QSettings
from PyQt4.QtGui import QFileDialog, QMessageBox, QStandardItemModel, QStandardItem
from dlg_file_connection import Ui_DlgFileConnection
from dlg_server_connections import Ui_DlgServerConnections
from dlg_edit_server_connection import Ui_DlgEditServerConnection
from dlg_about import Ui_DlgAbout
from dlg_progress import Ui_DlgProgress
from dlg_tile_reloading import Ui_DlgTileReloading
from options import Ui_OptionsGroup


_HELP_URL = "https://giswiki.hsr.ch/Vector_Tiles_Reader_QGIS_Plugin"


class AboutDialog(QtGui.QDialog, Ui_DlgAbout):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self._load_about()

    def _load_about(self):
        about_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "about.html")
        if os.path.isfile(about_path):
            with open(about_path, 'r') as f:
                html = f.read()
                self.txtAbout.setHtml(html)

    def show(self):
        self.exec_()


class OptionsGroup(QtGui.QGroupBox, Ui_OptionsGroup):

    def __init__(self, target_groupbox):
        self.setupUi(target_groupbox)
        self.lblZoomRange.setText("")
        self.chkLimitNrOfTiles.toggled.connect(lambda enabled: self.spinNrOfLoadedTiles.setEnabled(enabled))
        self.rbZoomManual.toggled.connect(lambda enabled: self.zoomSpin.setEnabled(enabled))

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

    def auto_load_tiles(self):
        return self.chkAutoLoadTiles.isChecked()

    def cartographic_ordering(self):
        return self.chkCartographicOrdering.isChecked()

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


class FileConnectionDialog(QtGui.QDialog, Ui_DlgFileConnection):

    on_valid_file_path_changed = pyqtSignal(str)
    on_open = pyqtSignal(str)

    def __init__(self, home_directory):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.options = OptionsGroup(self.grpOptions)

        self.path = None
        self.home_directory = home_directory
        self.btnBrowse.clicked.connect(self._open_browser)
        self.txtPath.textChanged.connect(self._on_path_changed)
        self.btnOpen.clicked.connect(self._handle_open_click)
        self.btnHelp.clicked.connect(lambda: webbrowser.open(_HELP_URL))
        self.lblError.setVisible(False)

    def show_error(self, error):
        self.lblError.setText(error)
        self.lblError.setVisible(True)

    def clear_path(self):
        self.txtPath.setText(None)
        self._update_open_button_state()
        # todo: why is the open button still enabled at this point?

    def hide_error(self):
        self.lblError.setVisible(False)

    def _open_browser(self):
        open_path = self.path
        if not open_path:
            open_path = self.home_directory

        open_file_name = QFileDialog.getOpenFileName(None, "Select Mapbox Tiles", open_path, "Mapbox Tiles (*.mbtiles)")

        if open_file_name:
            self.path = open_file_name
            self.txtPath.setText(open_file_name)

    def _on_path_changed(self):
        self.path = self.txtPath.text()
        self._update_open_button_state()

    def _update_open_button_state(self):
        is_valid_file = False
        if self.path:
            is_valid_file = os.path.isfile(self.path) and os.path.splitext(self.path)[1] == ".mbtiles"
            if not is_valid_file:
                self.show_error("This file does not exist or is not valid")
            else:
                self.hide_error()
        else:
            self.hide_error()
        if is_valid_file:
            self.on_valid_file_path_changed.emit(self.path)
        else:
            self.set_zoom(None, None)
        self.btnOpen.setEnabled(is_valid_file)

    def _handle_open_click(self):
        self.close()
        self.on_open.emit(self.path)

    def show(self):
        self.exec_()


class ProgressDialog(QtGui.QDialog, Ui_DlgProgress):
    on_cancel = pyqtSignal()

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi(self)
        self.lblMessage.setVisible(False)
        self.btnCancel.clicked.connect(self._on_cancel)
        self._is_loading = False

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


class TilesReloadingDialog(QtGui.QDialog, Ui_DlgTileReloading):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.always_accept = False
        self.always_deny = False

    def do_not_show_again(self):
        return self.chkDoNotShowAgain.isChecked()

    def reload_tiles(self):
        if self.always_accept:
            return True
        elif self.always_deny:
            return False

        result = self.exec_()
        if result == QtGui.QDialog.Accepted:
            self.always_accept = self.do_not_show_again()
            return True
        else:
            self.always_deny = self.do_not_show_again()
            return False


class ServerConnectionDialog(QtGui.QDialog, Ui_DlgServerConnections):

    on_connect = pyqtSignal(str)
    on_add = pyqtSignal(str)

    _connections_array = "connections"
    _table_headers = OrderedDict([
        ("ID", "id"),
        ("Min. Zoom", "minzoom"),
        ("Max. Zoom", "maxzoom"),
        ("Description", "description")
    ])

    _OMT = "OpenMapTiles.com (FreeTilehosting.com)"

    _predefined_connections = {_OMT: "http://free.tilehosting.com/data/v3.json?key={token}"}
    _tokens = {_OMT: "6irhAXGgsi8TrIDL0211"}

    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.grpCrs.setVisible(False)
        self.options = OptionsGroup(self.grpOptions)
        self.settings = QSettings("VtrSettings")
        self.connections = {}
        self.selected_connection = None
        self.selected_layer_id = None
        self.cbxConnections.currentIndexChanged['QString'].connect(self._handle_connection_change)
        self.btnCreateConnection.clicked.connect(self._create_connection)
        self.btnConnect.clicked.connect(self._on_connect)
        self.btnEdit.clicked.connect(self._edit_connection)
        self.btnDelete.clicked.connect(self._delete_connection)
        self.btnAdd.clicked.connect(self._load_tiles_for_connection)
        self.btnSave.clicked.connect(self._export_connections)
        self.btnLoad.clicked.connect(self._import_connections)
        self.btnHelp.clicked.connect(lambda: webbrowser.open(_HELP_URL))
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(self._table_headers.keys())
        self.tblLayers.setModel(self.model)
        self._load_connections()
        self._add_loaded_connections()

    def _load_tiles_for_connection(self):
        self.on_add.emit(self._get_current_connection()[1])

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
            if name not in self.connections:
                url = self._predefined_connections[name]
                self._set_connection_url(name, url)

        for name in self.connections:
            is_already_added = self.cbxConnections.findText(name) != -1
            if not is_already_added:
                self.cbxConnections.addItem(name)
        if len(self.connections) > 0:
            self.cbxConnections.setCurrentIndex(0)

    def _add_layer(self):
        self.on_add.emit(self._get_current_connection()[1])

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

    def _on_connect(self):
        conn = self._get_current_connection()
        url = conn[1]
        self.on_connect.emit(url)

    def _get_current_connection(self):
        name = self.cbxConnections.currentText()
        url = self.connections[name]
        if name in self._predefined_connections:
            url = url.replace("{token}", self._tokens[name])
        return name, url

    def show(self):
        self.exec_()

    def keep_dialog_open(self):
        return self.chkKeepOpen.isChecked()

    def set_layers(self, layers):
        self.model.removeRows(0, len(self.connections))
        for row_index, layer in enumerate(layers):
            for header_index, header in enumerate(self._table_headers.keys()):
                self.model.setItem(row_index, header_index, QStandardItem(str(layer[self._table_headers[header]])))
        add_enabled = layers is not None and len(layers) > 0
        self.btnAdd.setEnabled(add_enabled)

    def _edit_connection(self):
        conn = self._get_current_connection()
        self._create_or_update_connection(name=conn[0], url=conn[1])

    def _create_connection(self):
        self._create_or_update_connection()

    def _create_or_update_connection(self, name=None, url=None):
        dlg = EditServerConnection(name, url)
        result = dlg.exec_()
        if result == QtGui.QDialog.Accepted:
            newname, newurl = dlg.get_connection()
            self._set_connection_url(newname, newurl)
            if newname != name:
                self.cbxConnections.addItem(newname)
            self._save_connections()

    def _handle_connection_change(self, name):
        enable_connect = False
        enable_edit = False
        if name in self.connections:
            enable_connect = True
            enable_edit = name not in self._predefined_connections
        self.btnConnect.setEnabled(enable_connect)
        self.btnEdit.setEnabled(enable_edit)
        self.btnDelete.setEnabled(enable_edit)


class EditServerConnection(QtGui.QDialog, Ui_DlgEditServerConnection):
    def __init__(self, name=None, url=None):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.txtName.textChanged.connect(self._update_save_btn_state)
        self.txtUrl.textChanged.connect(self._update_save_btn_state)
        if name:
            self.txtName.setText(name)
        if url:
            self.txtUrl.setText(url)

    def _update_save_btn_state(self):
        enable = False
        if self.txtName.text() and self.txtUrl.text():
            enable = True
        self.btnSave.setEnabled(enable)

    def get_connection(self):
        return self.txtName.text(), self.txtUrl.text()

