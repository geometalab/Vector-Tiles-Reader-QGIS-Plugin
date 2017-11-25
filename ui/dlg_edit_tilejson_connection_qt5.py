# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlg_edit_tilejson_connection.ui'
#
# Created by: PyQt5 UI code generator 5.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DlgEditTileJSONConnection(object):
    def setupUi(self, DlgEditTileJSONConnection):
        DlgEditTileJSONConnection.setObjectName("DlgEditTileJSONConnection")
        DlgEditTileJSONConnection.resize(636, 154)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(DlgEditTileJSONConnection)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.groupBox = QtWidgets.QGroupBox(DlgEditTileJSONConnection)
        self.groupBox.setObjectName("groupBox")
        self.gridLayout = QtWidgets.QGridLayout(self.groupBox)
        self.gridLayout.setObjectName("gridLayout")
        self.txtName = QtWidgets.QLineEdit(self.groupBox)
        self.txtName.setText("")
        self.txtName.setObjectName("txtName")
        self.gridLayout.addWidget(self.txtName, 0, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.groupBox)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.lblTileJsonUrl = QtWidgets.QLabel(self.groupBox)
        self.lblTileJsonUrl.setObjectName("lblTileJsonUrl")
        self.gridLayout.addWidget(self.lblTileJsonUrl, 1, 0, 1, 1)
        self.txtUrl = QtWidgets.QLineEdit(self.groupBox)
        self.txtUrl.setText("")
        self.txtUrl.setPlaceholderText("")
        self.txtUrl.setObjectName("txtUrl")
        self.gridLayout.addWidget(self.txtUrl, 1, 1, 1, 1)
        self.txtStyleJsonUrl = QtWidgets.QLineEdit(self.groupBox)
        self.txtStyleJsonUrl.setObjectName("txtStyleJsonUrl")
        self.gridLayout.addWidget(self.txtStyleJsonUrl, 2, 1, 1, 1)
        self.lblServerStyleJsonUrl = QtWidgets.QLabel(self.groupBox)
        self.lblServerStyleJsonUrl.setObjectName("lblServerStyleJsonUrl")
        self.gridLayout.addWidget(self.lblServerStyleJsonUrl, 2, 0, 1, 1)
        self.verticalLayout_3.addWidget(self.groupBox)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.btnSave = QtWidgets.QPushButton(DlgEditTileJSONConnection)
        self.btnSave.setEnabled(False)
        self.btnSave.setCheckable(False)
        self.btnSave.setObjectName("btnSave")
        self.horizontalLayout.addWidget(self.btnSave)
        self.btnCancel = QtWidgets.QPushButton(DlgEditTileJSONConnection)
        self.btnCancel.setObjectName("btnCancel")
        self.horizontalLayout.addWidget(self.btnCancel)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.verticalLayout_3.setStretch(1, 1)

        self.retranslateUi(DlgEditTileJSONConnection)
        self.btnCancel.clicked.connect(DlgEditTileJSONConnection.reject)
        self.btnSave.clicked.connect(DlgEditTileJSONConnection.accept)
        QtCore.QMetaObject.connectSlotsByName(DlgEditTileJSONConnection)

    def retranslateUi(self, DlgEditTileJSONConnection):
        _translate = QtCore.QCoreApplication.translate
        DlgEditTileJSONConnection.setWindowTitle(_translate("DlgEditTileJSONConnection", "Edit Connection"))
        self.groupBox.setTitle(_translate("DlgEditTileJSONConnection", "Connection"))
        self.label.setText(_translate("DlgEditTileJSONConnection", "Name"))
        self.lblTileJsonUrl.setText(_translate("DlgEditTileJSONConnection", "TileJSON URL"))
        self.txtUrl.setToolTip(_translate("DlgEditTileJSONConnection", "The URL to the TileJSON of the tile service (e.g. http://yourtilehoster.com/index.json)"))
        self.lblServerStyleJsonUrl.setText(_translate("DlgEditTileJSONConnection", "StyleJSON URL"))
        self.btnSave.setText(_translate("DlgEditTileJSONConnection", "Save"))
        self.btnCancel.setText(_translate("DlgEditTileJSONConnection", "Cancel"))

