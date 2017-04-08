from PyQt4 import QtGui
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QFileDialog
from dlg_file_connection import Ui_DlgFileConnection
from dlg_server_connections import Ui_DlgServerConnections
from dlg_edit_server_connection import Ui_DlgEditServerConnection
from dlg_about import Ui_DlgAbout
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
        self.rbFile.toggled.connect(self._update_open_button_state)
        self.rbDirectory.toggled.connect(self._update_open_button_state)
        self.btnOpen.clicked.connect(self._handle_open_click)
        self.chkLimitNrOfTiles.toggled.connect(lambda enabled: self.spinNrOfLoadedTiles.setEnabled(enabled))
        self.rbZoomAuto.setEnabled(False)
        self.rbZoomManual.toggled.connect(lambda enabled: self.zoomSpin.setEnabled(enabled))
        self.lblError.setVisible(False)

    def show_error(self, error):
        self.lblError.setText(error)
        self.lblError.setVisible(True)

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

        if self.rbFile.isChecked():
            open_file_name = QFileDialog.getOpenFileName(None, "Select Mapbox Tiles", open_path, "Mapbox Tiles (*.mbtiles)")
        else:
            open_file_name = QFileDialog.getExistingDirectory(None, "Select Mapbox Tiles Directory", open_path)

        if open_file_name:
            self.path = open_file_name
            self.txtPath.setText(open_file_name)

    def _on_path_changed(self):
        self.path = self.txtPath.text()
        self._update_open_button_state()

    def _update_open_button_state(self):
        is_enabled = False
        if self.path:
            is_valid_dir = self.load_directory_checked() and os.path.isdir(self.path)
            is_valid_file = not self.load_directory_checked() and os.path.isfile(self.path) and os.path.splitext(self.path)[1] == ".mbtiles"
            is_enabled = is_valid_dir or is_valid_file
            if self.load_directory_checked() and not is_valid_dir:
                self.show_error("This is not a valid directory")
            elif not self.load_directory_checked() and not is_valid_file:
                self.show_error("This is not a valid mbtiles file")
            else:
                self.hide_error()
        else:
            self.hide_error()
        self.btnOpen.setEnabled(is_enabled)

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