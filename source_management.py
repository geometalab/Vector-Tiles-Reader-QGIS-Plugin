# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'source_management.ui'
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

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName(_fromUtf8("Dialog"))
        Dialog.resize(800, 364)
        self.tblSourceFiles = QtGui.QTableView(Dialog)
        self.tblSourceFiles.setGeometry(QtCore.QRect(10, 80, 781, 251))
        self.tblSourceFiles.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tblSourceFiles.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblSourceFiles.setObjectName(_fromUtf8("tblSourceFiles"))
        self.btnAdd = QtGui.QPushButton(Dialog)
        self.btnAdd.setGeometry(QtCore.QRect(10, 50, 51, 23))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/vectortilereader/add.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnAdd.setIcon(icon)
        self.btnAdd.setObjectName(_fromUtf8("btnAdd"))
        self.btnDelete = QtGui.QPushButton(Dialog)
        self.btnDelete.setGeometry(QtCore.QRect(60, 50, 75, 23))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/vectortilereader/delete.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnDelete.setIcon(icon1)
        self.btnDelete.setObjectName(_fromUtf8("btnDelete"))
        self.lblTitle = QtGui.QLabel(Dialog)
        self.lblTitle.setGeometry(QtCore.QRect(10, 10, 261, 16))
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.lblTitle.setFont(font)
        self.lblTitle.setObjectName(_fromUtf8("lblTitle"))
        self.btnClose = QtGui.QPushButton(Dialog)
        self.btnClose.setGeometry(QtCore.QRect(720, 340, 75, 23))
        self.btnClose.setObjectName(_fromUtf8("btnClose"))

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(_translate("Dialog", "Dialog", None))
        self.btnAdd.setText(_translate("Dialog", "Add", None))
        self.btnDelete.setText(_translate("Dialog", "Delete", None))
        self.lblTitle.setText(_translate("Dialog", "Mapbox File Management", None))
        self.btnClose.setText(_translate("Dialog", "Close", None))

import resources_rc
