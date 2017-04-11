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
        DlgProgress.resize(372, 58)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DlgProgress.sizePolicy().hasHeightForWidth())
        DlgProgress.setSizePolicy(sizePolicy)
        DlgProgress.setMinimumSize(QtCore.QSize(0, 0))
        DlgProgress.setMaximumSize(QtCore.QSize(600, 58))
        DlgProgress.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        DlgProgress.setModal(False)
        self.verticalLayout = QtGui.QVBoxLayout(DlgProgress)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.progressBar = QtGui.QProgressBar(DlgProgress)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setInvertedAppearance(False)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.verticalLayout.addWidget(self.progressBar)
        self.lblMessage = QtGui.QLabel(DlgProgress)
        self.lblMessage.setAlignment(QtCore.Qt.AlignCenter)
        self.lblMessage.setObjectName(_fromUtf8("lblMessage"))
        self.verticalLayout.addWidget(self.lblMessage)

        self.retranslateUi(DlgProgress)
        QtCore.QMetaObject.connectSlotsByName(DlgProgress)

    def retranslateUi(self, DlgProgress):
        DlgProgress.setWindowTitle(_translate("DlgProgress", "Loading Vector Tiles...", None))
        self.lblMessage.setText(_translate("DlgProgress", "TextLabel", None))

