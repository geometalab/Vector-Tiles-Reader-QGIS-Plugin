from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal, QSettings
from PyQt4.QtGui import QFileDialog, QMessageBox, QStandardItemModel, QStandardItem
from dlg_file_connection import Ui_DlgFileConnection
from dlg_server_connections import Ui_DlgServerConnections
from dlg_edit_server_connection import Ui_DlgEditServerConnection
from dlg_about import Ui_DlgAbout
from dlg_progress import Ui_DlgProgress
import os


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
        self.path = None
        self.home_directory = home_directory
        self.btnBrowse.clicked.connect(self._open_browser)
        self.txtPath.textChanged.connect(self._on_path_changed)
        self.btnOpen.clicked.connect(self._handle_open_click)
        self.chkLimitNrOfTiles.toggled.connect(lambda enabled: self.spinNrOfLoadedTiles.setEnabled(enabled))
        self.rbZoomAuto.setEnabled(False)
        self.rbZoomManual.toggled.connect(lambda enabled: self.zoomSpin.setEnabled(enabled))
        self.lblError.setVisible(False)
        self.lblZoomRange.setText("")

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

    def show_error(self, error):
        self.lblError.setText(error)
        self.lblError.setVisible(True)

    def clear_path(self):
        self.txtPath.setText(None)
        self._update_open_button_state()
        # todo: why is the open button still enabled at this point?

    def hide_error(self):
        self.lblError.setVisible(False)

    def load_directory_checked(self):
        return self.rbDirectory.isChecked()

    def get_manual_zoom(self):
        if not self.rbZoomManual.isChecked():
            return None
        return self.zoomSpin.value()

    def get_tile_number_limit(self):
        if not self.chkLimitNrOfTiles.isChecked():
            return None
        return self.spinNrOfLoadedTiles.value()

    def is_apply_styles_enabled(self):
        return self.chkApplyStyles.isChecked()

    def is_merge_tiles_enabled(self):
        return self.chkMergeTiles.isChecked()

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
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.lblMessage.setVisible(False)

    def set_maximum(self, max):
        self.progressBar.setMaximum(max)

    def set_progress(self, value):
        self.progressBar.setValue(value)

    def set_message(self, msg=None):
        self.lblMessage.setText(msg)
        if msg:
            self.lblMessage.setVisible(True)
        else:
            self.lblMessage.setVisible(False)

    def open(self):
        self.show()

    def hide(self):
        self.close()


class ServerConnectionDialog(QtGui.QDialog, Ui_DlgServerConnections):

    on_connect = pyqtSignal(str)
    on_add = pyqtSignal()

    _connections_array = "connections"
    _table_headers = ["ID"]

    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.settings = QSettings("VtrSettings")
        self.connections = {}
        self.selected_connection = None
        self.selected_layer_id = None
        self.cbxConnections.currentIndexChanged['QString'].connect(self._handle_connection_change)
        self.btnCreateConnection.clicked.connect(self._create_connection)
        self.btnConnect.clicked.connect(self._on_connect)
        self.btnDelete.clicked.connect(self._delete_connection)
        self.btnAdd.clicked.connect(self.on_add)
        self._load_connections()

    def _load_connections(self):
        settings = self.settings
        connections = settings.beginReadArray(self._connections_array)
        for i in range(connections):
            settings.setArrayIndex(i)
            name = settings.value("name")
            url = settings.value("url")
            self._add_connection(name, url)
        settings.endArray()
        self.cbxConnections.addItems(self.connections.keys())
        if len(self.connections) > 0:
            self.cbxConnections.setCurrentIndex(0)

    def apply_styles_enabled(self):
        return self.chkApplyStyles.isChecked()

    def merge_tiles_enabled(self):
        return self.chkMergeTiles.isChecked()

    # def _selected_layer_changed(self):
    #     layer_id = None
    #     for index in self.tblLayers.selectionModel().selectedRows():
    #         layer_id = index.data()
    #         print("selected: {}".format(layer_id))
    #         break
    #     self.btnAdd.setEnabled(layer_id is not None)
    #     self.selected_layer_id = layer_id

    def _add_layer(self):
        self.on_add.emit(self.selected_layer_id)

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

    def _add_connection(self, name, url):
        self.connections[name] = url

    def _on_connect(self):
        name = self.cbxConnections.currentText()
        if name in self.connections:
            self.on_connect.emit(self.connections[name])

    def show(self):
        self.exec_()

    def set_layers(self, layers):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(self._table_headers)
        for l in layers:
            item = QStandardItem(l["id"])
            item.setEditable(False)
            model.appendRow(item)
        self.tblLayers.setModel(model)
        add_enabled = layers is not None and len(layers) > 0
        self.btnAdd.setEnabled(add_enabled)
        # self.tblLayers.selectionModel().selectionChanged.connect(self._selected_layer_changed)

    def _create_connection(self):
        dlg = EditServerConnection()
        result = dlg.exec_()
        print(result)
        if result == QtGui.QDialog.Accepted:
            name, url = dlg.get_connection()
            self._add_connection(name, url)
            self.cbxConnections.addItem(name)
            self._save_connections()

    def _handle_connection_change(self, name):
        print("connection changed to: {}".format(name))
        enable = False
        if name in self.connections:
            enable = True
        self.btnConnect.setEnabled(enable)
        self.btnEdit.setEnabled(enable)
        self.btnDelete.setEnabled(enable)


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

