from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QColor, QAction, QIcon, QMenu, QToolButton, QFileDialog, QMessageBox
from dlg_file_connection import Ui_DlgFileConnection
from dlg_server_connections import Ui_DlgServerConnections
from dlg_edit_server_connection import Ui_DlgEditServerConnection
import os
# from file_helper import FileHelper
# from vt_reader import VtReader


class FileConnectionDialog(QtGui.QDialog, Ui_DlgFileConnection):

    path_changed = pyqtSignal(str)

    def __init__(self, iface, on_open_file):
        QtGui.QDialog.__init__(self)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        self.btnBrowse.clicked.connect(self._open_browser)
        self.txtPath.textChanged.connect(self._on_path_changed)
        self.rbFile.toggled.connect(self._on_type_changed)
        self.rbDirectory.toggled.connect(self._on_type_changed)
        # self.btnOpen.clicked.connect(lambda e: on_open_file(self.path))

    def set_min_zoom(self, zoom):
        self.zoomSpin.setMinimum(zoom)

    def set_max_zoom(self, zoom):
        self.zoomSpin.setMaximum(zoom)

    def set_open_button_enabled(self, is_enabled):
        self.btnOpen.setEnabled(is_enabled)

    def _open_browser(self):
        if self.rbFile.isChecked():
            self.path = QFileDialog.getOpenFileName(self, "Select Mapbox Tiles", "", "Mapbox Tiles (*.mbtiles)")
        else:
            self.path = QFileDialog.getExistingDirectory(self, "Select Mapbox Tiles Directory", "")

        self.txtPath.setText(self.path)

    def _on_type_changed(self):
        if self.rbDirectory.isChecked() and self.path:
            self.txtPath.setText(os.path.dirname(self.path))
        else:
            self.txtPath.setText(None)

    def _on_path_changed(self):
        self.path = self.txtPath.text()
        if not self.path:
            self.path = None
            self.set_open_button_enabled(False)
        self.path_changed.emit(self.path)

    def show(self):
        self.exec_()


class ServerConnectionDialog(QtGui.QDialog, Ui_DlgServerConnections):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)


class EditServerConnection(QtGui.QDialog, Ui_DlgEditServerConnection):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)