# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt/connections_group.ui'
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

class Ui_ConnectionsGroup(object):
    def setupUi(self, ConnectionsGroup):
        ConnectionsGroup.setObjectName(_fromUtf8("ConnectionsGroup"))
        ConnectionsGroup.resize(508, 100)
        self.verticalLayout = QtGui.QVBoxLayout(ConnectionsGroup)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.cbxConnections = QtGui.QComboBox(ConnectionsGroup)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbxConnections.sizePolicy().hasHeightForWidth())
        self.cbxConnections.setSizePolicy(sizePolicy)
        self.cbxConnections.setObjectName(_fromUtf8("cbxConnections"))
        self.verticalLayout.addWidget(self.cbxConnections)
        self.horizontalLayout_3 = QtGui.QHBoxLayout()
        self.horizontalLayout_3.setSizeConstraint(QtGui.QLayout.SetMinimumSize)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.btnConnect = QtGui.QPushButton(ConnectionsGroup)
        self.btnConnect.setEnabled(False)
        self.btnConnect.setObjectName(_fromUtf8("btnConnect"))
        self.horizontalLayout_3.addWidget(self.btnConnect)
        self.btnCreateConnection = QtGui.QPushButton(ConnectionsGroup)
        self.btnCreateConnection.setObjectName(_fromUtf8("btnCreateConnection"))
        self.horizontalLayout_3.addWidget(self.btnCreateConnection)
        self.btnEdit = QtGui.QPushButton(ConnectionsGroup)
        self.btnEdit.setEnabled(False)
        self.btnEdit.setObjectName(_fromUtf8("btnEdit"))
        self.horizontalLayout_3.addWidget(self.btnEdit)
        self.btnDelete = QtGui.QPushButton(ConnectionsGroup)
        self.btnDelete.setEnabled(False)
        self.btnDelete.setMaximumSize(QtCore.QSize(80, 16777215))
        self.btnDelete.setObjectName(_fromUtf8("btnDelete"))
        self.horizontalLayout_3.addWidget(self.btnDelete)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.btnLoad = QtGui.QPushButton(ConnectionsGroup)
        self.btnLoad.setMaximumSize(QtCore.QSize(80, 16777215))
        self.btnLoad.setObjectName(_fromUtf8("btnLoad"))
        self.horizontalLayout_3.addWidget(self.btnLoad)
        self.btnSave = QtGui.QPushButton(ConnectionsGroup)
        self.btnSave.setMaximumSize(QtCore.QSize(80, 16777215))
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.horizontalLayout_3.addWidget(self.btnSave)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.retranslateUi(ConnectionsGroup)
        QtCore.QMetaObject.connectSlotsByName(ConnectionsGroup)

    def retranslateUi(self, ConnectionsGroup):
        ConnectionsGroup.setWindowTitle(_translate("ConnectionsGroup", "Connections", None))
        ConnectionsGroup.setTitle(_translate("ConnectionsGroup", "Connections", None))
        self.btnConnect.setText(_translate("ConnectionsGroup", "Connect", None))
        self.btnCreateConnection.setText(_translate("ConnectionsGroup", "New", None))
        self.btnEdit.setText(_translate("ConnectionsGroup", "Edit", None))
        self.btnDelete.setText(_translate("ConnectionsGroup", "Delete", None))
        self.btnLoad.setText(_translate("ConnectionsGroup", "Load", None))
        self.btnSave.setText(_translate("ConnectionsGroup", "Save", None))

