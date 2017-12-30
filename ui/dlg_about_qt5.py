# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlg_about.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_DlgAbout(object):
    def setupUi(self, DlgAbout):
        DlgAbout.setObjectName("DlgAbout")
        DlgAbout.resize(382, 372)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
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
        self.txtAbout.setHtml(_translate("DlgAbout", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol\'; font-size:12pt; font-weight:600; color:#24292e;\">Vector Tiles Reader Plugin</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol\'; font-size:10pt; color:#24292e;\">Maintained by the </span><span style=\" font-family:\'-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol\'; font-size:10pt; font-weight:600; color:#24292e;\">Geometa Lab HSR</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol\'; font-size:10pt; color:#24292e;\">Developed by Martin Boos.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol\'; font-size:10pt; color:#24292e;\">Visit the plugin on </span><a href=\"https://github.com/geometalab/Vector-Tiles-Reader-QGIS-Plugin\"><span style=\" font-size:8pt; text-decoration: underline; color:#0000ff;\">Github</span></a><span style=\" font-family:\'-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol\'; font-size:10pt; color:#24292e;\"> or report issues </span><a href=\"https://github.com/geometalab/Vector-Tiles-Reader-QGIS-Plugin/issues\"><span style=\" font-size:8pt; text-decoration: underline; color:#0000ff;\">here</span></a><span style=\" font-family:\'-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol\'; font-size:10pt; color:#24292e;\">.</span></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol\'; font-size:10pt; color:#24292e;\">Homepage: </span><a href=\"http://giswiki.hsr.ch/Vector_Tiles_Reader_QGIS_Plugin\"><span style=\" font-size:8pt; text-decoration: underline; color:#0000ff;\">http://giswiki.hsr.ch/Vector_Tiles_Reader_QGIS_Plugin</span></a></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol\'; font-size:10pt; color:#24292e;\">Get own free key for OpenMapTiles from </span><a href=\"https://openmaptiles.com/hosting/\"><span style=\" font-size:8pt; text-decoration: underline; color:#0000ff;\">OpenMapTiles.com</span></a></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a href=\"http://www.openstreetmap.org\"><span style=\" font-family:\'-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol\'; font-size:10pt; text-decoration: underline; color:#0000ff;\">http://www.openstreetmap.org</span></a></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol\'; font-size:10pt; font-weight:600; color:#24292e;\">Contributions:</span><span style=\" font-family:\'-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif,Apple Color Emoji,Segoe UI Emoji,Segoe UI Symbol\'; font-size:10pt; color:#24292e;\"><br />- Stefan Keller<br />- Dijan Helbling<br />- Nicola Jordan<br />- Raphael Das Gupta<br />- Carmelo Schumacher</span></p></body></html>"))

