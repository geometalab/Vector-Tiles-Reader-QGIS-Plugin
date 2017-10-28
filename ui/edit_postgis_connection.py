# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'edit_postgis_connection.ui'
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

class Ui_PostgisConnectionGroup(object):
    def setupUi(self, PostgisConnectionGroup):
        PostgisConnectionGroup.setObjectName(_fromUtf8("PostgisConnectionGroup"))
        PostgisConnectionGroup.resize(400, 227)
        self.gridLayout = QtGui.QGridLayout(PostgisConnectionGroup)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblpgPassword = QtGui.QLabel(PostgisConnectionGroup)
        self.lblpgPassword.setObjectName(_fromUtf8("lblpgPassword"))
        self.gridLayout.addWidget(self.lblpgPassword, 3, 0, 1, 1)
        self.lblpgPort = QtGui.QLabel(PostgisConnectionGroup)
        self.lblpgPort.setObjectName(_fromUtf8("lblpgPort"))
        self.gridLayout.addWidget(self.lblpgPort, 1, 0, 1, 1)
        self.txtpgPort = QtGui.QLineEdit(PostgisConnectionGroup)
        self.txtpgPort.setObjectName(_fromUtf8("txtpgPort"))
        self.gridLayout.addWidget(self.txtpgPort, 1, 1, 1, 1)
        self.lblpgHost = QtGui.QLabel(PostgisConnectionGroup)
        self.lblpgHost.setObjectName(_fromUtf8("lblpgHost"))
        self.gridLayout.addWidget(self.lblpgHost, 0, 0, 1, 1)
        self.txtpgUsername = QtGui.QLineEdit(PostgisConnectionGroup)
        self.txtpgUsername.setObjectName(_fromUtf8("txtpgUsername"))
        self.gridLayout.addWidget(self.txtpgUsername, 2, 1, 1, 1)
        self.txtpgPassword = QtGui.QLineEdit(PostgisConnectionGroup)
        self.txtpgPassword.setObjectName(_fromUtf8("txtpgPassword"))
        self.gridLayout.addWidget(self.txtpgPassword, 3, 1, 1, 1)
        self.lblpgDatabase = QtGui.QLabel(PostgisConnectionGroup)
        self.lblpgDatabase.setObjectName(_fromUtf8("lblpgDatabase"))
        self.gridLayout.addWidget(self.lblpgDatabase, 4, 0, 1, 1)
        self.comboBox = QtGui.QComboBox(PostgisConnectionGroup)
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        self.gridLayout.addWidget(self.comboBox, 4, 1, 1, 1)
        self.txtpgHost = QtGui.QLineEdit(PostgisConnectionGroup)
        self.txtpgHost.setObjectName(_fromUtf8("txtpgHost"))
        self.gridLayout.addWidget(self.txtpgHost, 0, 1, 1, 1)
        self.lblpgUsername = QtGui.QLabel(PostgisConnectionGroup)
        self.lblpgUsername.setObjectName(_fromUtf8("lblpgUsername"))
        self.gridLayout.addWidget(self.lblpgUsername, 2, 0, 1, 1)
        self.chkpgStorePassword = QtGui.QCheckBox(PostgisConnectionGroup)
        self.chkpgStorePassword.setChecked(True)
        self.chkpgStorePassword.setObjectName(_fromUtf8("chkpgStorePassword"))
        self.gridLayout.addWidget(self.chkpgStorePassword, 5, 0, 1, 2)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 6, 0, 1, 1)

        self.retranslateUi(PostgisConnectionGroup)
        QtCore.QMetaObject.connectSlotsByName(PostgisConnectionGroup)

    def retranslateUi(self, PostgisConnectionGroup):
        PostgisConnectionGroup.setWindowTitle(_translate("PostgisConnectionGroup", "GroupBox", None))
        PostgisConnectionGroup.setTitle(_translate("PostgisConnectionGroup", "Connection Information", None))
        self.lblpgPassword.setText(_translate("PostgisConnectionGroup", "Password", None))
        self.lblpgPort.setText(_translate("PostgisConnectionGroup", "Port", None))
        self.lblpgHost.setText(_translate("PostgisConnectionGroup", "Host", None))
        self.lblpgDatabase.setText(_translate("PostgisConnectionGroup", "Database", None))
        self.lblpgUsername.setText(_translate("PostgisConnectionGroup", "Username", None))
        self.chkpgStorePassword.setText(_translate("PostgisConnectionGroup", "Save Password", None))

