# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlg_edit_connection.ui'
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

class Ui_DlgEditConnection(object):
    def setupUi(self, DlgEditConnection):
        DlgEditConnection.setObjectName(_fromUtf8("DlgEditConnection"))
        DlgEditConnection.resize(562, 131)
        self.verticalLayout_3 = QtGui.QVBoxLayout(DlgEditConnection)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.groupBox = QtGui.QGroupBox(DlgEditConnection)
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.gridLayout = QtGui.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.txtName = QtGui.QLineEdit(self.groupBox)
        self.txtName.setText(_fromUtf8(""))
        self.txtName.setObjectName(_fromUtf8("txtName"))
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.txtUrl = QtGui.QLineEdit(self.groupBox)
        self.txtUrl.setText(_fromUtf8(""))
        self.txtUrl.setPlaceholderText(_fromUtf8(""))
        self.txtUrl.setObjectName(_fromUtf8("txtUrl"))
        self.gridLayout.addWidget(self.txtUrl, 1, 1, 1, 1)
        self.label = QtGui.QLabel(self.groupBox)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.lblTileJsonUrl = QtGui.QLabel(self.groupBox)
        self.lblTileJsonUrl.setObjectName(_fromUtf8("lblTileJsonUrl"))
        self.gridLayout.addWidget(self.lblTileJsonUrl, 1, 0, 1, 1)
        self.verticalLayout_3.addWidget(self.groupBox)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnSave = QtGui.QPushButton(DlgEditConnection)
        self.btnSave.setEnabled(False)
        self.btnSave.setCheckable(False)
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.horizontalLayout.addWidget(self.btnSave)
        self.btnCancel = QtGui.QPushButton(DlgEditConnection)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.horizontalLayout.addWidget(self.btnCancel)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout_3.setStretch(1, 1)

        self.retranslateUi(DlgEditConnection)
        QtCore.QObject.connect(self.btnCancel, QtCore.SIGNAL(_fromUtf8("clicked()")), DlgEditConnection.reject)
        QtCore.QObject.connect(self.btnSave, QtCore.SIGNAL(_fromUtf8("clicked()")), DlgEditConnection.accept)
        QtCore.QMetaObject.connectSlotsByName(DlgEditConnection)

    def retranslateUi(self, DlgEditConnection):
        DlgEditConnection.setWindowTitle(_translate("DlgEditConnection", "Edit Connection", None))
        self.groupBox.setTitle(_translate("DlgEditConnection", "Connection", None))
        self.txtUrl.setToolTip(_translate("DlgEditConnection", "The URL to the TileJSON of the tile service (e.g. http://yourtilehoster.com/index.json)", None))
        self.label.setText(_translate("DlgEditConnection", "Name", None))
        self.lblTileJsonUrl.setText(_translate("DlgEditConnection", "TileJSON URL", None))
        self.btnSave.setText(_translate("DlgEditConnection", "Save", None))
        self.btnCancel.setText(_translate("DlgEditConnection", "Cancel", None))

