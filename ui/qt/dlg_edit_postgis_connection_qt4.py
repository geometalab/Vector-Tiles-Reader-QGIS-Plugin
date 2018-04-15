# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt/dlg_edit_postgis_connection.ui'
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
        DlgEditPostgisConnection.resize(523, 253)
        self.gridLayout = QtGui.QGridLayout(DlgEditPostgisConnection)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.btnCancel = QtGui.QPushButton(DlgEditPostgisConnection)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.gridLayout.addWidget(self.btnCancel, 1, 2, 1, 1)
        self.btnSave = QtGui.QPushButton(DlgEditPostgisConnection)
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.gridLayout.addWidget(self.btnSave, 1, 1, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.Connection = QtGui.QGroupBox(DlgEditPostgisConnection)
        self.Connection.setObjectName(_fromUtf8("Connection"))
        self.gridLayout_2 = QtGui.QGridLayout(self.Connection)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.txtpgName = QtGui.QLineEdit(self.Connection)
        self.txtpgName.setObjectName(_fromUtf8("txtpgName"))
        self.gridLayout_2.addWidget(self.txtpgName, 0, 2, 1, 1)
        self.lblpgHost = QtGui.QLabel(self.Connection)
        self.lblpgHost.setObjectName(_fromUtf8("lblpgHost"))
        self.gridLayout_2.addWidget(self.lblpgHost, 1, 0, 1, 1)
        self.lblpgUsername = QtGui.QLabel(self.Connection)
        self.lblpgUsername.setObjectName(_fromUtf8("lblpgUsername"))
        self.gridLayout_2.addWidget(self.lblpgUsername, 3, 0, 1, 1)
        self.txtpgUsername = QtGui.QLineEdit(self.Connection)
        self.txtpgUsername.setObjectName(_fromUtf8("txtpgUsername"))
        self.gridLayout_2.addWidget(self.txtpgUsername, 3, 2, 1, 1)
        self.lblpgPort = QtGui.QLabel(self.Connection)
        self.lblpgPort.setObjectName(_fromUtf8("lblpgPort"))
        self.gridLayout_2.addWidget(self.lblpgPort, 2, 0, 1, 1)
        self.txtpgHost = QtGui.QLineEdit(self.Connection)
        self.txtpgHost.setObjectName(_fromUtf8("txtpgHost"))
        self.gridLayout_2.addWidget(self.txtpgHost, 1, 2, 1, 1)
        self.lblpgDatabase = QtGui.QLabel(self.Connection)
        self.lblpgDatabase.setObjectName(_fromUtf8("lblpgDatabase"))
        self.gridLayout_2.addWidget(self.lblpgDatabase, 5, 0, 1, 1)
        self.lblpgPassword = QtGui.QLabel(self.Connection)
        self.lblpgPassword.setObjectName(_fromUtf8("lblpgPassword"))
        self.gridLayout_2.addWidget(self.lblpgPassword, 4, 0, 1, 1)
        self.lblpgName = QtGui.QLabel(self.Connection)
        self.lblpgName.setObjectName(_fromUtf8("lblpgName"))
        self.gridLayout_2.addWidget(self.lblpgName, 0, 0, 1, 1)
        self.txtpgPassword = QtGui.QLineEdit(self.Connection)
        self.txtpgPassword.setEchoMode(QtGui.QLineEdit.Password)
        self.txtpgPassword.setObjectName(_fromUtf8("txtpgPassword"))
        self.gridLayout_2.addWidget(self.txtpgPassword, 4, 2, 1, 1)
        self.chkpgStorePassword = QtGui.QCheckBox(self.Connection)
        self.chkpgStorePassword.setChecked(True)
        self.chkpgStorePassword.setObjectName(_fromUtf8("chkpgStorePassword"))
        self.gridLayout_2.addWidget(self.chkpgStorePassword, 6, 0, 1, 3)
        self.spinpgPort = QtGui.QSpinBox(self.Connection)
        self.spinpgPort.setButtonSymbols(QtGui.QAbstractSpinBox.NoButtons)
        self.spinpgPort.setMinimum(0)
        self.spinpgPort.setMaximum(65535)
        self.spinpgPort.setObjectName(_fromUtf8("spinpgPort"))
        self.gridLayout_2.addWidget(self.spinpgPort, 2, 2, 1, 1)
        self.txtpgDatabase = QtGui.QLineEdit(self.Connection)
        self.txtpgDatabase.setObjectName(_fromUtf8("txtpgDatabase"))
        self.gridLayout_2.addWidget(self.txtpgDatabase, 5, 2, 1, 1)
        self.gridLayout.addWidget(self.Connection, 0, 0, 1, 3)

        self.retranslateUi(DlgEditPostgisConnection)
        QtCore.QObject.connect(self.btnCancel, QtCore.SIGNAL(_fromUtf8("clicked()")), DlgEditPostgisConnection.reject)
        QtCore.QObject.connect(self.btnSave, QtCore.SIGNAL(_fromUtf8("clicked()")), DlgEditPostgisConnection.accept)
        QtCore.QMetaObject.connectSlotsByName(DlgEditPostgisConnection)
        DlgEditPostgisConnection.setTabOrder(self.txtpgName, self.txtpgHost)
        DlgEditPostgisConnection.setTabOrder(self.txtpgHost, self.spinpgPort)
        DlgEditPostgisConnection.setTabOrder(self.spinpgPort, self.txtpgUsername)
        DlgEditPostgisConnection.setTabOrder(self.txtpgUsername, self.txtpgPassword)
        DlgEditPostgisConnection.setTabOrder(self.txtpgPassword, self.chkpgStorePassword)
        DlgEditPostgisConnection.setTabOrder(self.chkpgStorePassword, self.btnSave)
        DlgEditPostgisConnection.setTabOrder(self.btnSave, self.btnCancel)

    def retranslateUi(self, DlgEditPostgisConnection):
        DlgEditPostgisConnection.setWindowTitle(_translate("DlgEditPostgisConnection", "Dialog", None))
        self.btnCancel.setText(_translate("DlgEditPostgisConnection", "Cancel", None))
        self.btnSave.setText(_translate("DlgEditPostgisConnection", "Save", None))
        self.Connection.setTitle(_translate("DlgEditPostgisConnection", "GroupBox", None))
        self.lblpgHost.setText(_translate("DlgEditPostgisConnection", "Host", None))
        self.lblpgUsername.setText(_translate("DlgEditPostgisConnection", "Username", None))
        self.lblpgPort.setText(_translate("DlgEditPostgisConnection", "Port", None))
        self.lblpgDatabase.setText(_translate("DlgEditPostgisConnection", "Database", None))
        self.lblpgPassword.setText(_translate("DlgEditPostgisConnection", "Password", None))
        self.lblpgName.setText(_translate("DlgEditPostgisConnection", "Name", None))
        self.chkpgStorePassword.setText(_translate("DlgEditPostgisConnection", "Save Password", None))

