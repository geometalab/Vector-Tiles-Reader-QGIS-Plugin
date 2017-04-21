# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlg_edit_server_connection.ui'
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

class Ui_DlgEditServerConnection(object):
    def setupUi(self, DlgEditServerConnection):
        DlgEditServerConnection.setObjectName(_fromUtf8("DlgEditServerConnection"))
        DlgEditServerConnection.resize(520, 132)
        self.verticalLayout_3 = QtGui.QVBoxLayout(DlgEditServerConnection)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.groupBox = QtGui.QGroupBox(DlgEditServerConnection)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.horizontalLayout_3.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setContentsMargins(10, -1, -1, -1)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.txtName = QtGui.QLineEdit(self.groupBox)
        self.txtName.setText(_fromUtf8(""))
        self.txtName.setObjectName(_fromUtf8("txtName"))
        self.verticalLayout_2.addWidget(self.txtName)
        self.txtUrl = QtGui.QLineEdit(self.groupBox)
        self.txtUrl.setText(_fromUtf8(""))
        self.txtUrl.setPlaceholderText(_fromUtf8(""))
        self.txtUrl.setObjectName(_fromUtf8("txtUrl"))
        self.verticalLayout_2.addWidget(self.txtUrl)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.gridLayout.addLayout(self.horizontalLayout_3, 0, 0, 1, 1)
        self.verticalLayout_3.addWidget(self.groupBox)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnSave = QtGui.QPushButton(DlgEditServerConnection)
        self.btnSave.setEnabled(False)
        self.btnSave.setCheckable(False)
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.horizontalLayout.addWidget(self.btnSave)
        self.btnCancel = QtGui.QPushButton(DlgEditServerConnection)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.horizontalLayout.addWidget(self.btnCancel)
        self.verticalLayout_3.addLayout(self.horizontalLayout)

        self.retranslateUi(DlgEditServerConnection)
        QtCore.QObject.connect(self.btnCancel, QtCore.SIGNAL(_fromUtf8("clicked()")), DlgEditServerConnection.reject)
        QtCore.QObject.connect(self.btnSave, QtCore.SIGNAL(_fromUtf8("clicked()")), DlgEditServerConnection.accept)
        QtCore.QMetaObject.connectSlotsByName(DlgEditServerConnection)

    def retranslateUi(self, DlgEditServerConnection):
        DlgEditServerConnection.setWindowTitle(_translate("DlgEditServerConnection", "Edit Connection", None))
        self.groupBox.setTitle(_translate("DlgEditServerConnection", "Connection", None))
        self.label.setText(_translate("DlgEditServerConnection", "Name", None))
        self.label_2.setText(_translate("DlgEditServerConnection", "TileJSON URL", None))
        self.txtUrl.setToolTip(_translate("DlgEditServerConnection", "The URL to the TileJSON of the tile service (e.g. http://yourtilehoster.com/index.json)", None))
        self.btnSave.setText(_translate("DlgEditServerConnection", "Save", None))
        self.btnCancel.setText(_translate("DlgEditServerConnection", "Cancel", None))

