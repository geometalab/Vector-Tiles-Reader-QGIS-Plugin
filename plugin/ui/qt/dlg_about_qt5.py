# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'qt/dlg_about.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_DlgAbout(object):
    def setupUi(self, DlgAbout):
        DlgAbout.setObjectName("DlgAbout")
        DlgAbout.resize(475, 477)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DlgAbout.sizePolicy().hasHeightForWidth())
        DlgAbout.setSizePolicy(sizePolicy)
        self.gridLayout = QtWidgets.QGridLayout(DlgAbout)
        self.gridLayout.setObjectName("gridLayout")
        self.btnClose = QtWidgets.QPushButton(DlgAbout)
        self.btnClose.setMinimumSize(QtCore.QSize(80, 0))
        self.btnClose.setObjectName("btnClose")
        self.gridLayout.addWidget(self.btnClose, 1, 0, 1, 1, QtCore.Qt.AlignRight)
        self.txtAbout = QtWidgets.QTextBrowser(DlgAbout)
        self.txtAbout.setMinimumSize(QtCore.QSize(350, 240))
        self.txtAbout.setOpenExternalLinks(True)
        self.txtAbout.setObjectName("txtAbout")
        self.gridLayout.addWidget(self.txtAbout, 0, 0, 1, 1)

        self.retranslateUi(DlgAbout)
        self.btnClose.clicked.connect(DlgAbout.reject)
        QtCore.QMetaObject.connectSlotsByName(DlgAbout)

    def retranslateUi(self, DlgAbout):
        _translate = QtCore.QCoreApplication.translate
        DlgAbout.setWindowTitle(_translate("DlgAbout", "About Vector Tile Reader"))
        self.btnClose.setText(_translate("DlgAbout", "Close"))
        self.txtAbout.setHtml(
            _translate(
                "DlgAbout",
                '',
            )
        )
