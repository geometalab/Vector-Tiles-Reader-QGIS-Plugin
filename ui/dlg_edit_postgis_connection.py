# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlg_edit_postgis_connection.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_DlgEditPostgisConnection(object):
    def setupUi(self, DlgEditPostgisConnection):
        DlgEditPostgisConnection.setObjectName(_fromUtf8("DlgEditPostgisConnection"))
        DlgEditPostgisConnection.resize(523, 256)
        self.gridLayout = QtGui.QGridLayout(DlgEditPostgisConnection)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.Connection = QtGui.QGroupBox(DlgEditPostgisConnection)
        self.Connection.setObjectName(_fromUtf8("Connection"))
        self.gridLayout_2 = QtGui.QGridLayout(self.Connection)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.lblpgHost = QtGui.QLabel(self.Connection)
        self.lblpgHost.setObjectName(_fromUtf8("lblpgHost"))
        self.gridLayout_2.addWidget(self.lblpgHost, 1, 0, 1, 1)
        self.lblpgUsername = QtGui.QLabel(self.Connection)
        self.lblpgUsername.setObjectName(_fromUtf8("lblpgUsername"))
        self.gridLayout_2.addWidget(self.lblpgUsername, 3, 0, 1, 1)
        self.txtpgPort = QtGui.QLineEdit(self.Connection)
        self.txtpgPort.setObjectName(_fromUtf8("txtpgPort"))
        self.gridLayout_2.addWidget(self.txtpgPort, 2, 1, 1, 1)
        self.txtpgUsername = QtGui.QLineEdit(self.Connection)
        self.txtpgUsername.setObjectName(_fromUtf8("txtpgUsername"))
        self.gridLayout_2.addWidget(self.txtpgUsername, 3, 1, 1, 1)
        self.lblpgPort = QtGui.QLabel(self.Connection)
        self.lblpgPort.setObjectName(_fromUtf8("lblpgPort"))
        self.gridLayout_2.addWidget(self.lblpgPort, 2, 0, 1, 1)
        self.txtpgHost = QtGui.QLineEdit(self.Connection)
        self.txtpgHost.setObjectName(_fromUtf8("txtpgHost"))
        self.gridLayout_2.addWidget(self.txtpgHost, 1, 1, 1, 1)
        self.lblpgDatabase = QtGui.QLabel(self.Connection)
        self.lblpgDatabase.setObjectName(_fromUtf8("lblpgDatabase"))
        self.gridLayout_2.addWidget(self.lblpgDatabase, 5, 0, 1, 1)
        self.comboBox = QtGui.QComboBox(self.Connection)
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        self.gridLayout_2.addWidget(self.comboBox, 5, 1, 1, 1)
        self.lblpgPassword = QtGui.QLabel(self.Connection)
        self.lblpgPassword.setObjectName(_fromUtf8("lblpgPassword"))
        self.gridLayout_2.addWidget(self.lblpgPassword, 4, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 23, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem, 7, 0, 1, 1)
        self.txtpgPassword = QtGui.QLineEdit(self.Connection)
        self.txtpgPassword.setObjectName(_fromUtf8("txtpgPassword"))
        self.gridLayout_2.addWidget(self.txtpgPassword, 4, 1, 1, 1)
        self.chkpgStorePassword = QtGui.QCheckBox(self.Connection)
        self.chkpgStorePassword.setChecked(True)
        self.chkpgStorePassword.setObjectName(_fromUtf8("chkpgStorePassword"))
        self.gridLayout_2.addWidget(self.chkpgStorePassword, 6, 0, 1, 2)
        self.txtpgName = QtGui.QLineEdit(self.Connection)
        self.txtpgName.setObjectName(_fromUtf8("txtpgName"))
        self.gridLayout_2.addWidget(self.txtpgName, 0, 1, 1, 1)
        self.lblpgName = QtGui.QLabel(self.Connection)
        self.lblpgName.setObjectName(_fromUtf8("lblpgName"))
        self.gridLayout_2.addWidget(self.lblpgName, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.Connection, 0, 0, 1, 1)

        self.retranslateUi(DlgEditPostgisConnection)
        QtCore.QMetaObject.connectSlotsByName(DlgEditPostgisConnection)

    def retranslateUi(self, DlgEditPostgisConnection):
        DlgEditPostgisConnection.setWindowTitle(_translate("DlgEditPostgisConnection", "Dialog", None))
        self.Connection.setTitle(_translate("DlgEditPostgisConnection", "GroupBox", None))
        self.lblpgHost.setText(_translate("DlgEditPostgisConnection", "Host", None))
        self.lblpgUsername.setText(_translate("DlgEditPostgisConnection", "Username", None))
        self.lblpgPort.setText(_translate("DlgEditPostgisConnection", "Port", None))
        self.lblpgDatabase.setText(_translate("DlgEditPostgisConnection", "Database", None))
        self.lblpgPassword.setText(_translate("DlgEditPostgisConnection", "Password", None))
        self.chkpgStorePassword.setText(_translate("DlgEditPostgisConnection", "Save Password", None))
        self.lblpgName.setText(_translate("DlgEditPostgisConnection", "Name", None))

