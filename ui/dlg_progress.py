# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlg_progress.ui'
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

class Ui_DlgProgress(object):
    def setupUi(self, DlgProgress):
        DlgProgress.setObjectName(_fromUtf8("DlgProgress"))
        DlgProgress.setWindowModality(QtCore.Qt.NonModal)
        DlgProgress.resize(369, 87)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DlgProgress.sizePolicy().hasHeightForWidth())
        DlgProgress.setSizePolicy(sizePolicy)
        DlgProgress.setMinimumSize(QtCore.QSize(0, 0))
        DlgProgress.setMaximumSize(QtCore.QSize(600, 87))
        DlgProgress.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        DlgProgress.setModal(False)
        self.gridLayout = QtGui.QGridLayout(DlgProgress)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblMessage = QtGui.QLabel(DlgProgress)
        self.lblMessage.setAlignment(QtCore.Qt.AlignCenter)
        self.lblMessage.setObjectName(_fromUtf8("lblMessage"))
        self.gridLayout.addWidget(self.lblMessage, 1, 0, 1, 1)
        self.progressBar = QtGui.QProgressBar(DlgProgress)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setInvertedAppearance(False)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridLayout.addWidget(self.progressBar, 0, 0, 1, 2)
        self.btnCancel = QtGui.QPushButton(DlgProgress)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.gridLayout.addWidget(self.btnCancel, 2, 0, 1, 1, QtCore.Qt.AlignRight)
        self.gridLayout.setColumnStretch(0, 1)

        self.retranslateUi(DlgProgress)
        QtCore.QMetaObject.connectSlotsByName(DlgProgress)

    def retranslateUi(self, DlgProgress):
        DlgProgress.setWindowTitle(_translate("DlgProgress", "Loading Vector Tiles...", None))
        self.lblMessage.setText(_translate("DlgProgress", "TextLabel", None))
        self.btnCancel.setText(_translate("DlgProgress", "Cancel", None))

