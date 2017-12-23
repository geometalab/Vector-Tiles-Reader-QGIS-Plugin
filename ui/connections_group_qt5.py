# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'connections_group.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_ConnectionsGroup(object):
    def setupUi(self, ConnectionsGroup):
        ConnectionsGroup.setObjectName("ConnectionsGroup")
        ConnectionsGroup.resize(508, 100)
        self.verticalLayout = QtWidgets.QVBoxLayout(ConnectionsGroup)
        self.verticalLayout.setObjectName("verticalLayout")
        self.cbxConnections = QtWidgets.QComboBox(ConnectionsGroup)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cbxConnections.sizePolicy().hasHeightForWidth())
        self.cbxConnections.setSizePolicy(sizePolicy)
        self.cbxConnections.setObjectName("cbxConnections")
        self.verticalLayout.addWidget(self.cbxConnections)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.btnConnect = QtWidgets.QPushButton(ConnectionsGroup)
        self.btnConnect.setEnabled(False)
        self.btnConnect.setObjectName("btnConnect")
        self.horizontalLayout_3.addWidget(self.btnConnect)
        self.btnCreateConnection = QtWidgets.QPushButton(ConnectionsGroup)
        self.btnCreateConnection.setObjectName("btnCreateConnection")
        self.horizontalLayout_3.addWidget(self.btnCreateConnection)
        self.btnEdit = QtWidgets.QPushButton(ConnectionsGroup)
        self.btnEdit.setEnabled(False)
        self.btnEdit.setObjectName("btnEdit")
        self.horizontalLayout_3.addWidget(self.btnEdit)
        self.btnDelete = QtWidgets.QPushButton(ConnectionsGroup)
        self.btnDelete.setEnabled(False)
        self.btnDelete.setMaximumSize(QtCore.QSize(80, 16777215))
        self.btnDelete.setObjectName("btnDelete")
        self.horizontalLayout_3.addWidget(self.btnDelete)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem)
        self.btnLoad = QtWidgets.QPushButton(ConnectionsGroup)
        self.btnLoad.setMaximumSize(QtCore.QSize(80, 16777215))
        self.btnLoad.setObjectName("btnLoad")
        self.horizontalLayout_3.addWidget(self.btnLoad)
        self.btnSave = QtWidgets.QPushButton(ConnectionsGroup)
        self.btnSave.setMaximumSize(QtCore.QSize(80, 16777215))
        self.btnSave.setObjectName("btnSave")
        self.horizontalLayout_3.addWidget(self.btnSave)
        self.verticalLayout.addLayout(self.horizontalLayout_3)

        self.retranslateUi(ConnectionsGroup)
        QtCore.QMetaObject.connectSlotsByName(ConnectionsGroup)

    def retranslateUi(self, ConnectionsGroup):
        _translate = QtCore.QCoreApplication.translate
        ConnectionsGroup.setWindowTitle(_translate("ConnectionsGroup", "Connections"))
        ConnectionsGroup.setTitle(_translate("ConnectionsGroup", "Connections"))
        self.btnConnect.setText(_translate("ConnectionsGroup", "Connect"))
        self.btnCreateConnection.setText(_translate("ConnectionsGroup", "New"))
        self.btnEdit.setText(_translate("ConnectionsGroup", "Edit"))
        self.btnDelete.setText(_translate("ConnectionsGroup", "Delete"))
        self.btnLoad.setText(_translate("ConnectionsGroup", "Load"))
        self.btnSave.setText(_translate("ConnectionsGroup", "Save"))

