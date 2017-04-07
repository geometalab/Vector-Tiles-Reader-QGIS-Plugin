from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QColor, QAction, QIcon, QMenu, QToolButton, QFileDialog, QMessageBox
from dlg_file_connection import Ui_DlgFileConnection
from dlg_server_connections import Ui_DlgServerConnections
from dlg_edit_server_connection import Ui_DlgEditServerConnection
import os


class FileConnectionDialog(QtGui.QDialog, Ui_DlgFileConnection):

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
        self.rbFile.toggled.connect(self._on_type_changed)
        self.rbDirectory.toggled.connect(self._on_type_changed)
        self.btnOpen.clicked.connect(self._handle_open_click)

    def load_directory_checked(self):
        return self.rbDirectory.isChecked()

    def is_apply_styles_enabled(self):
        return self.chkApplyStyles.isChecked()

    def is_merge_tiles_enabled(self):
        return self.chkMergeTiles.isChecked()

    def _open_browser(self):
        open_path = self.path
        if not open_path:
            open_path = self.home_directory

        if self.rbFile.isChecked():
            open_file_name = QFileDialog.getOpenFileName(None, "Select Mapbox Tiles", open_path, "Mapbox Tiles (*.mbtiles)")
        else:
            open_file_name = QFileDialog.getExistingDirectory(None, "Select Mapbox Tiles Directory", open_path)

        if open_file_name:
            self.path = open_file_name
            self.txtPath.setText(open_file_name)

    def _on_type_changed(self):
        if self.rbDirectory.isChecked() and self.path:
            directory = self.path
            if os.path.isfile(directory):
                directory = os.path.dirname(self.path)
            self.txtPath.setText(directory)
        else:
            self.txtPath.setText(None)

    def _on_path_changed(self):
        self.path = self.txtPath.text()
        has_path = True
        if not self.path:
            self.path = None
            has_path = False
        self.btnOpen.setEnabled(has_path)

    def _handle_open_click(self):
        self.close()
        self.on_open.emit(self.path)

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