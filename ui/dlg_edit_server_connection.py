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
        DlgEditServerConnection.resize(582, 231)
        self.groupBox = QtGui.QGroupBox(DlgEditServerConnection)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 561, 91))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.layoutWidget_2 = QtGui.QWidget(self.groupBox)
        self.layoutWidget_2.setGeometry(QtCore.QRect(10, 20, 531, 50))
        self.layoutWidget_2.setObjectName(_fromUtf8("layoutWidget_2"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.layoutWidget_2)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.layoutWidget_2)
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.label_2 = QtGui.QLabel(self.layoutWidget_2)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.verticalLayout.addWidget(self.label_2)
        self.horizontalLayout_3.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setContentsMargins(10, -1, -1, -1)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.lineEdit = QtGui.QLineEdit(self.layoutWidget_2)
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.verticalLayout_2.addWidget(self.lineEdit)
        self.lineEdit_2 = QtGui.QLineEdit(self.layoutWidget_2)
        self.lineEdit_2.setObjectName(_fromUtf8("lineEdit_2"))
        self.verticalLayout_2.addWidget(self.lineEdit_2)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.groupBox_2 = QtGui.QGroupBox(DlgEditServerConnection)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 110, 561, 71))
        self.groupBox_2.setObjectName(_fromUtf8("groupBox_2"))
        self.layoutWidget_3 = QtGui.QWidget(self.groupBox_2)
        self.layoutWidget_3.setGeometry(QtCore.QRect(10, 20, 209, 42))
        self.layoutWidget_3.setObjectName(_fromUtf8("layoutWidget_3"))
        self.verticalLayout_4 = QtGui.QVBoxLayout(self.layoutWidget_3)
        self.verticalLayout_4.setObjectName(_fromUtf8("verticalLayout_4"))
        self.checkBox_3 = QtGui.QCheckBox(self.layoutWidget_3)
        self.checkBox_3.setObjectName(_fromUtf8("checkBox_3"))
        self.verticalLayout_4.addWidget(self.checkBox_3)
        self.checkBox_4 = QtGui.QCheckBox(self.layoutWidget_3)
        self.checkBox_4.setObjectName(_fromUtf8("checkBox_4"))
        self.verticalLayout_4.addWidget(self.checkBox_4)
        self.layoutWidget = QtGui.QWidget(DlgEditServerConnection)
        self.layoutWidget.setGeometry(QtCore.QRect(410, 200, 158, 25))
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.layoutWidget)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.btnSave = QtGui.QPushButton(self.layoutWidget)
        self.btnSave.setObjectName(_fromUtf8("btnSave"))
        self.horizontalLayout.addWidget(self.btnSave)
        self.btnCancel = QtGui.QPushButton(self.layoutWidget)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.horizontalLayout.addWidget(self.btnCancel)

        self.retranslateUi(DlgEditServerConnection)
        QtCore.QMetaObject.connectSlotsByName(DlgEditServerConnection)

    def retranslateUi(self, DlgEditServerConnection):
        DlgEditServerConnection.setWindowTitle(_translate("DlgEditServerConnection", "Edit Connection", None))
        self.groupBox.setTitle(_translate("DlgEditServerConnection", "Connection", None))
        self.label.setText(_translate("DlgEditServerConnection", "Name", None))
        self.label_2.setText(_translate("DlgEditServerConnection", "URL", None))
        self.groupBox_2.setTitle(_translate("DlgEditServerConnection", "Options", None))
        self.checkBox_3.setText(_translate("DlgEditServerConnection", "Apply Styles (disable for performance)", None))
        self.checkBox_4.setText(_translate("DlgEditServerConnection", "Merge Tiles (disable for performance)", None))
        self.btnSave.setText(_translate("DlgEditServerConnection", "Save", None))
        self.btnCancel.setText(_translate("DlgEditServerConnection", "Cancel", None))

