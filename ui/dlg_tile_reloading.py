# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlg_tile_reloading.ui'
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

class Ui_DlgTileReloading(object):
    def setupUi(self, DlgTileReloading):
        DlgTileReloading.setObjectName(_fromUtf8("DlgTileReloading"))
        DlgTileReloading.resize(400, 118)
        self.gridLayout = QtGui.QGridLayout(DlgTileReloading)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.chkDoNotShowAgain = QtGui.QCheckBox(DlgTileReloading)
        self.chkDoNotShowAgain.setObjectName(_fromUtf8("chkDoNotShowAgain"))
        self.horizontalLayout.addWidget(self.chkDoNotShowAgain, QtCore.Qt.AlignLeft)
        self.btnOk = QtGui.QPushButton(DlgTileReloading)
        self.btnOk.setMinimumSize(QtCore.QSize(0, 0))
        self.btnOk.setMaximumSize(QtCore.QSize(70, 16777215))
        self.btnOk.setObjectName(_fromUtf8("btnOk"))
        self.horizontalLayout.addWidget(self.btnOk, QtCore.Qt.AlignRight)
        self.btnCancel = QtGui.QPushButton(DlgTileReloading)
        self.btnCancel.setMaximumSize(QtCore.QSize(70, 16777215))
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.horizontalLayout.addWidget(self.btnCancel, QtCore.Qt.AlignRight)
        self.horizontalLayout.setStretch(0, 1)
        self.gridLayout.addLayout(self.horizontalLayout, 1, 0, 1, 1)
        self.label = QtGui.QLabel(DlgTileReloading)
        self.label.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.label.setWordWrap(True)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.gridLayout.setRowStretch(0, 1)

        self.retranslateUi(DlgTileReloading)
        QtCore.QObject.connect(self.btnOk, QtCore.SIGNAL(_fromUtf8("clicked()")), DlgTileReloading.accept)
        QtCore.QObject.connect(self.btnCancel, QtCore.SIGNAL(_fromUtf8("clicked()")), DlgTileReloading.reject)
        QtCore.QMetaObject.connectSlotsByName(DlgTileReloading)

    def retranslateUi(self, DlgTileReloading):
        DlgTileReloading.setWindowTitle(_translate("DlgTileReloading", "Tile Reloading", None))
        self.chkDoNotShowAgain.setText(_translate("DlgTileReloading", "Do not show again", None))
        self.btnOk.setText(_translate("DlgTileReloading", "Yes", None))
        self.btnCancel.setText(_translate("DlgTileReloading", "No", None))
        self.label.setText(_translate("DlgTileReloading", "Warning: New tiles will be loaded for the newly visible extent. Depending on the current map scale, this may take a while. You will still be able to cancel the loading process manually.\n"
"\n"
"Do you want to continue?", None))

