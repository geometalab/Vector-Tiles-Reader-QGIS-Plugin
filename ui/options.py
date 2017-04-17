# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'options.ui'
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

class Ui_OptionsGroup(object):
    def setupUi(self, OptionsGroup):
        OptionsGroup.setObjectName(_fromUtf8("OptionsGroup"))
        OptionsGroup.resize(391, 202)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(OptionsGroup.sizePolicy().hasHeightForWidth())
        OptionsGroup.setSizePolicy(sizePolicy)
        self.gridLayout = QtGui.QGridLayout(OptionsGroup)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.chkMergeTiles = QtGui.QCheckBox(OptionsGroup)
        self.chkMergeTiles.setChecked(False)
        self.chkMergeTiles.setObjectName(_fromUtf8("chkMergeTiles"))
        self.gridLayout.addWidget(self.chkMergeTiles, 0, 0, 1, 2)
        self.label_5 = QtGui.QLabel(OptionsGroup)
        self.label_5.setMaximumSize(QtCore.QSize(16777215, 20))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 2, 0, 1, 1)
        self.rbZoomMax = QtGui.QRadioButton(OptionsGroup)
        self.rbZoomMax.setChecked(True)
        self.rbZoomMax.setObjectName(_fromUtf8("rbZoomMax"))
        self.gridLayout.addWidget(self.rbZoomMax, 2, 1, 1, 1)
        self.gridLayout_5 = QtGui.QGridLayout()
        self.gridLayout_5.setHorizontalSpacing(6)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.spinNrOfLoadedTiles = QtGui.QSpinBox(OptionsGroup)
        self.spinNrOfLoadedTiles.setEnabled(False)
        self.spinNrOfLoadedTiles.setMinimumSize(QtCore.QSize(0, 21))
        self.spinNrOfLoadedTiles.setMinimum(1)
        self.spinNrOfLoadedTiles.setMaximum(9999)
        self.spinNrOfLoadedTiles.setProperty("value", 10)
        self.spinNrOfLoadedTiles.setObjectName(_fromUtf8("spinNrOfLoadedTiles"))
        self.gridLayout_5.addWidget(self.spinNrOfLoadedTiles, 1, 1, 1, 1, QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.chkLimitNrOfTiles = QtGui.QCheckBox(OptionsGroup)
        self.chkLimitNrOfTiles.setObjectName(_fromUtf8("chkLimitNrOfTiles"))
        self.gridLayout_5.addWidget(self.chkLimitNrOfTiles, 1, 0, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_5.addItem(spacerItem, 1, 2, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_5, 1, 0, 1, 2)
        self.chkApplyStyles = QtGui.QCheckBox(OptionsGroup)
        self.chkApplyStyles.setChecked(True)
        self.chkApplyStyles.setObjectName(_fromUtf8("chkApplyStyles"))
        self.gridLayout.addWidget(self.chkApplyStyles, 6, 0, 1, 2)
        self.rbZoomAuto = QtGui.QRadioButton(OptionsGroup)
        self.rbZoomAuto.setObjectName(_fromUtf8("rbZoomAuto"))
        self.gridLayout.addWidget(self.rbZoomAuto, 3, 1, 1, 1)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.rbZoomManual = QtGui.QRadioButton(OptionsGroup)
        self.rbZoomManual.setText(_fromUtf8(""))
        self.rbZoomManual.setObjectName(_fromUtf8("rbZoomManual"))
        self.horizontalLayout.addWidget(self.rbZoomManual)
        self.zoomSpin = QtGui.QSpinBox(OptionsGroup)
        self.zoomSpin.setEnabled(False)
        self.zoomSpin.setMaximumSize(QtCore.QSize(70, 16777215))
        self.zoomSpin.setObjectName(_fromUtf8("zoomSpin"))
        self.horizontalLayout.addWidget(self.zoomSpin, QtCore.Qt.AlignLeft)
        self.lblZoomRange = QtGui.QLabel(OptionsGroup)
        self.lblZoomRange.setObjectName(_fromUtf8("lblZoomRange"))
        self.horizontalLayout.addWidget(self.lblZoomRange)
        spacerItem1 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.gridLayout.addLayout(self.horizontalLayout, 4, 1, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.gridLayout.addItem(spacerItem2, 5, 0, 1, 1)

        self.retranslateUi(OptionsGroup)
        QtCore.QMetaObject.connectSlotsByName(OptionsGroup)

    def retranslateUi(self, OptionsGroup):
        OptionsGroup.setWindowTitle(_translate("OptionsGroup", "Options", None))
        OptionsGroup.setTitle(_translate("OptionsGroup", "Options", None))
        self.chkMergeTiles.setText(_translate("OptionsGroup", "Merge Tiles (disable for performance)", None))
        self.label_5.setText(_translate("OptionsGroup", "Zoom", None))
        self.rbZoomMax.setText(_translate("OptionsGroup", "Max. Zoom", None))
        self.chkLimitNrOfTiles.setText(_translate("OptionsGroup", "Limit the number of loaded tiles", None))
        self.chkApplyStyles.setToolTip(_translate("OptionsGroup", "Apply a build-in, predefined QGIS style made for OpenMapTiles (instead of random QGIS default style)", None))
        self.chkApplyStyles.setText(_translate("OptionsGroup", "Apply predefined OpenMapTiles style", None))
        self.rbZoomAuto.setText(_translate("OptionsGroup", "Auto (scale-dependent)", None))
        self.lblZoomRange.setText(_translate("OptionsGroup", "TextLabel", None))

