# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlg_server_connections.ui'
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

class Ui_DlgServerConnections(object):
    def setupUi(self, DlgServerConnections):
        DlgServerConnections.setObjectName(_fromUtf8("DlgServerConnections"))
        DlgServerConnections.resize(781, 465)
        DlgServerConnections.setSizeGripEnabled(True)
        self.layoutWidget = QtGui.QWidget(DlgServerConnections)
        self.layoutWidget.setGeometry(QtCore.QRect(500, 430, 269, 25))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.checkBox = QtGui.QCheckBox(self.layoutWidget)
        self.checkBox.setObjectName(_fromUtf8("checkBox"))
        self.horizontalLayout.addWidget(self.checkBox)
        self.btnAdd = QtGui.QPushButton(self.layoutWidget)
        self.btnAdd.setObjectName(_fromUtf8("btnAdd"))
        self.horizontalLayout.addWidget(self.btnAdd)
        self.btnClose = QtGui.QPushButton(self.layoutWidget)
        self.btnClose.setObjectName(_fromUtf8("btnClose"))
        self.horizontalLayout.addWidget(self.btnClose)
        self.groupBox = QtGui.QGroupBox(DlgServerConnections)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 761, 80))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.comboBox = QtGui.QComboBox(self.groupBox)
        self.comboBox.setGeometry(QtCore.QRect(10, 20, 741, 22))
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        self.layoutWidget_2 = QtGui.QWidget(self.groupBox)
        self.layoutWidget_2.setGeometry(QtCore.QRect(10, 50, 320, 25))
        self.layoutWidget_2.setObjectName(_fromUtf8("layoutWidget_2"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.layoutWidget_2)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.btnConnect = QtGui.QPushButton(self.layoutWidget_2)
        self.btnConnect.setObjectName(_fromUtf8("btnConnect"))
        self.horizontalLayout_2.addWidget(self.btnConnect)
        self.pushButton = QtGui.QPushButton(self.layoutWidget_2)
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.horizontalLayout_2.addWidget(self.pushButton)
        self.pushButton_2 = QtGui.QPushButton(self.layoutWidget_2)
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.horizontalLayout_2.addWidget(self.pushButton_2)
        self.pushButton_3 = QtGui.QPushButton(self.layoutWidget_2)
        self.pushButton_3.setMaximumSize(QtCore.QSize(80, 16777215))
        self.pushButton_3.setObjectName(_fromUtf8("pushButton_3"))
        self.horizontalLayout_2.addWidget(self.pushButton_3)
        self.layoutWidget_3 = QtGui.QWidget(self.groupBox)
        self.layoutWidget_3.setGeometry(QtCore.QRect(589, 50, 161, 25))
        self.layoutWidget_3.setObjectName(_fromUtf8("layoutWidget_3"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.layoutWidget_3)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.btnLoad = QtGui.QPushButton(self.layoutWidget_3)
        self.btnLoad.setMaximumSize(QtCore.QSize(80, 16777215))
        self.btnLoad.setObjectName(_fromUtf8("btnLoad"))
        self.horizontalLayout_3.addWidget(self.btnLoad)
        self.btnSave = QtGui.QPushButton(self.layoutWidget_3)
        self.btnSave.setMaximumSize(QtCore.QSize(80, 16777215))
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.horizontalLayout_3.addWidget(self.btnSave, QtCore.Qt.AlignRight)
        self.groupBox_2 = QtGui.QGroupBox(DlgServerConnections)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 300, 761, 71))
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.layoutWidget_4 = QtGui.QWidget(self.groupBox_2)
        self.layoutWidget_4.setGeometry(QtCore.QRect(10, 20, 209, 42))
        self.layoutWidget_4.setObjectName(_fromUtf8("layoutWidget_4"))
        self.verticalLayout_5 = QtGui.QVBoxLayout(self.layoutWidget_4)
        self.verticalLayout_5.setObjectName(_fromUtf8("verticalLayout_5"))
        self.chkApplyStyles = QtGui.QCheckBox(self.layoutWidget_4)
        self.chkApplyStyles.setChecked(True)
        self.chkApplyStyles.setObjectName(_fromUtf8("chkApplyStyles"))
        self.verticalLayout_5.addWidget(self.chkApplyStyles)
        self.chkMergeTiles = QtGui.QCheckBox(self.layoutWidget_4)
        self.chkMergeTiles.setChecked(True)
        self.chkMergeTiles.setObjectName(_fromUtf8("chkMergeTiles"))
        self.verticalLayout_5.addWidget(self.chkMergeTiles)
        self.groupBox_3 = QtGui.QGroupBox(DlgServerConnections)
        self.groupBox_3.setGeometry(QtCore.QRect(10, 380, 761, 41))
        self.groupBox_3.setObjectName(_fromUtf8("groupBox_3"))
        self.lblCrs = QtGui.QLabel(self.groupBox_3)
        self.lblCrs.setGeometry(QtCore.QRect(10, 20, 91, 16))
        self.lblCrs.setObjectName(_fromUtf8("lblCrs"))
        self.btnChangeCrs = QtGui.QPushButton(self.groupBox_3)
        self.btnChangeCrs.setGeometry(QtCore.QRect(680, 10, 75, 23))
        self.btnChangeCrs.setObjectName(_fromUtf8("btnChangeCrs"))
        self.tblLayers = QtGui.QTableView(DlgServerConnections)
        self.tblLayers.setGeometry(QtCore.QRect(10, 100, 761, 192))
        self.tblLayers.setObjectName(_fromUtf8("tblLayers"))

        self.retranslateUi(DlgServerConnections)
        QtCore.QMetaObject.connectSlotsByName(DlgServerConnections)

    def retranslateUi(self, DlgServerConnections):
        DlgServerConnections.setWindowTitle(_translate("DlgServerConnections", "Add Layer(s) from a Vector Tile Server", None))
        self.checkBox.setText(_translate("DlgServerConnections", "Keep dialog open", None))
        self.btnAdd.setText(_translate("DlgServerConnections", "Add", None))
        self.btnClose.setText(_translate("DlgServerConnections", "Close", None))
        self.groupBox.setTitle(_translate("DlgServerConnections", "Server connections", None))
        self.btnConnect.setText(_translate("DlgServerConnections", "Connect", None))
        self.pushButton.setText(_translate("DlgServerConnections", "New", None))
        self.pushButton_2.setText(_translate("DlgServerConnections", "Edit", None))
        self.pushButton_3.setText(_translate("DlgServerConnections", "Delete", None))
        self.btnLoad.setText(_translate("DlgServerConnections", "Load", None))
        self.btnSave.setText(_translate("DlgServerConnections", "Save", None))
        self.groupBox_2.setTitle(_translate("DlgServerConnections", "Options", None))
        self.chkApplyStyles.setText(_translate("DlgServerConnections", "Apply Styles (disable for performance)", None))
        self.chkMergeTiles.setText(_translate("DlgServerConnections", "Merge Tiles (disable for performance)", None))
        self.groupBox_3.setTitle(_translate("DlgServerConnections", "Coordinate reference system", None))
        self.lblCrs.setText(_translate("DlgServerConnections", "not implemented", None))
        self.btnChangeCrs.setText(_translate("DlgServerConnections", "Change", None))

