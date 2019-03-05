import copy
import csv
from ..util.log_helper import info
from .qt.connections_group_qt5 import Ui_ConnectionsGroup
from ..util.connection import ConnectionTypes
from PyQt5.QtWidgets import QGroupBox, QFileDialog, QMessageBox, QDialog
from PyQt5.QtCore import pyqtSignal
from typing import Dict


class ConnectionsGroup(QGroupBox, Ui_ConnectionsGroup):

    on_connect = pyqtSignal(dict)
    on_connection_change = pyqtSignal("QString")

    def __init__(
        self, target_groupbox, edit_dialog, connection_template, settings_key, settings, predefined_connections=None
    ):
        super(QGroupBox, self).__init__()

        self._connection_template = connection_template
        cloned_predefined_connections = {}
        if predefined_connections:
            for name in predefined_connections:
                predefined_connection = predefined_connections[name]
                clone = self._apply_template_connection(predefined_connection)
                cloned_predefined_connections[name] = clone
        self._predefined_connections: Dict[str, dict] = cloned_predefined_connections

        self.setupUi(target_groupbox)
        self._settings = settings
        self._settings_key = settings_key
        self.btnConnect.clicked.connect(self._handle_connect)
        self.btnEdit.clicked.connect(self._edit_connection)
        self.btnDelete.clicked.connect(self._delete_connection)
        self.btnSave.clicked.connect(self._export_connections)
        self.btnLoad.clicked.connect(self._import_connections)
        self.cbxConnections.currentIndexChanged["QString"].connect(self._handle_connection_change)
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
        for key in connection:
            if key not in clone:
                info("Key '{}' could not be found in the connection template!", key)
        return clone

    def _handle_connect(self):
        conn = self.get_current_connection()
        self.on_connect.emit(conn)

    def _export_connections(self):
        file_name = QFileDialog.getSaveFileName(None, "Export Vector Tile Reader Connections", "", "csv (*.csv)")
        if isinstance(file_name, tuple):
            file_name = file_name[0]
        if file_name:
            with open(file_name, "w") as csvfile:
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
        open_file_name = QFileDialog.getOpenFileName(None, "Export Vector Tile Reader Connections", "", "csv (*.csv)")
        if isinstance(open_file_name, tuple):
            open_file_name = open_file_name[0]
        if open_file_name:
            with open(open_file_name, "r") as csvfile:
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
                conn = self._predefined_connections[name]
                disabled = "disabled" in conn and conn["disabled"]
                if name not in self.connections:
                    if not disabled:
                        self.connections[name] = conn
                else:
                    if disabled:
                        del self.connections[name]

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
        reply = QMessageBox.question(self.activateWindow(), "Confirm Delete", msg, QMessageBox.Yes, QMessageBox.No)
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
        conn = self.get_current_connection()
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
                can_edit = predefined_connection.get("can_edit")
            enable_edit = not is_predefined_connection or can_edit in ["true", True]
        self.btnConnect.setEnabled(enable_connect)
        self.btnEdit.setEnabled(enable_edit)
        self.btnDelete.setEnabled(not is_predefined_connection)
        self.on_connection_change.emit(name)

    def get_current_connection(self):
        """
        * Returns the currently selected connection.
        * The {token} in the URL is replaced, so that the URL can be used.
        :return:
        """
        name = self.cbxConnections.currentText()
        connection = copy.deepcopy(self.connections[name])
        if self._predefined_connections and name in self._predefined_connections and connection["token"]:
            connection["url"] = connection["url"].replace("{token}", connection["token"])
            connection["style"] = connection["style"].replace("{token}", connection["token"])
        return connection
