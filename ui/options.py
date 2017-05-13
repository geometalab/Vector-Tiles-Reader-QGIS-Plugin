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
        OptionsGroup.resize(391, 225)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(OptionsGroup.sizePolicy().hasHeightForWidth())
        OptionsGroup.setSizePolicy(sizePolicy)
        self.gridLayout = QtGui.QGridLayout(OptionsGroup)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.rbZoomMax = QtGui.QRadioButton(OptionsGroup)
        self.rbZoomMax.setChecked(True)
        self.rbZoomMax.setObjectName(_fromUtf8("rbZoomMax"))
        self.gridLayout.addWidget(self.rbZoomMax, 5, 1, 1, 1)
        self.chkAutoLoadTiles = QtGui.QCheckBox(OptionsGroup)
        self.chkAutoLoadTiles.setChecked(False)
        self.chkAutoLoadTiles.setObjectName(_fromUtf8("chkAutoLoadTiles"))
        self.gridLayout.addWidget(self.chkAutoLoadTiles, 3, 0, 1, 2)
        self.chkApplyStyles = QtGui.QCheckBox(OptionsGroup)
        self.chkApplyStyles.setChecked(True)
        self.chkApplyStyles.setObjectName(_fromUtf8("chkApplyStyles"))
        self.gridLayout.addWidget(self.chkApplyStyles, 8, 0, 1, 2)
        spacerItem = QtGui.QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.gridLayout.addItem(spacerItem, 7, 0, 1, 1)
        self.chkCartographicOrdering = QtGui.QCheckBox(OptionsGroup)
        self.chkCartographicOrdering.setChecked(True)
        self.chkCartographicOrdering.setObjectName(_fromUtf8("chkCartographicOrdering"))
        self.gridLayout.addWidget(self.chkCartographicOrdering, 2, 0, 1, 2)
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
        self.gridLayout.addLayout(self.horizontalLayout, 6, 1, 1, 1)
        self.label_5 = QtGui.QLabel(OptionsGroup)
        self.label_5.setMaximumSize(QtCore.QSize(16777215, 20))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.gridLayout.addWidget(self.label_5, 5, 0, 1, 1)
        self.gridLayout_5 = QtGui.QGridLayout()
        self.gridLayout_5.setHorizontalSpacing(6)
        self.gridLayout_5.setObjectName(_fromUtf8("gridLayout_5"))
        self.spinNrOfLoadedTiles = QtGui.QSpinBox(OptionsGroup)
        self.spinNrOfLoadedTiles.setEnabled(True)
        self.spinNrOfLoadedTiles.setMinimumSize(QtCore.QSize(0, 21))
        self.spinNrOfLoadedTiles.setMinimum(1)
        self.spinNrOfLoadedTiles.setMaximum(9999)
        self.spinNrOfLoadedTiles.setProperty("value", 20)
        self.spinNrOfLoadedTiles.setObjectName(_fromUtf8("spinNrOfLoadedTiles"))
        self.gridLayout_5.addWidget(self.spinNrOfLoadedTiles, 1, 1, 1, 1, QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.chkLimitNrOfTiles = QtGui.QCheckBox(OptionsGroup)
        self.chkLimitNrOfTiles.setChecked(True)
        self.chkLimitNrOfTiles.setObjectName(_fromUtf8("chkLimitNrOfTiles"))
        self.gridLayout_5.addWidget(self.chkLimitNrOfTiles, 1, 0, 1, 1)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout_5.addItem(spacerItem2, 1, 2, 1, 1)
        self.gridLayout.addLayout(self.gridLayout_5, 1, 0, 1, 2)
        self.chkMergeTiles = QtGui.QCheckBox(OptionsGroup)
        self.chkMergeTiles.setChecked(False)
        self.chkMergeTiles.setObjectName(_fromUtf8("chkMergeTiles"))
        self.gridLayout.addWidget(self.chkMergeTiles, 4, 0, 1, 2)

        self.retranslateUi(OptionsGroup)
        QtCore.QMetaObject.connectSlotsByName(OptionsGroup)

    def retranslateUi(self, OptionsGroup):
        OptionsGroup.setWindowTitle(_translate("OptionsGroup", "Options", None))
        OptionsGroup.setTitle(_translate("OptionsGroup", "Options", None))
        self.rbZoomMax.setText(_translate("OptionsGroup", "Max. Zoom", None))
        self.chkAutoLoadTiles.setText(_translate("OptionsGroup", "Automatically load tiles for visible area", None))
        self.chkApplyStyles.setToolTip(_translate("OptionsGroup", "Apply a build-in, predefined QGIS style made for OpenMapTiles (instead of random QGIS default style)", None))
        self.chkApplyStyles.setText(_translate("OptionsGroup", "Apply predefined OpenMapTiles style", None))
        self.chkCartographicOrdering.setToolTip(_translate("OptionsGroup", "Use ordering according to cartographic element types (label, points, lines, areas) instead of original ordering from the tile source", None))
        self.chkCartographicOrdering.setText(_translate("OptionsGroup", "Cartographic layer ordering", None))
        self.lblZoomRange.setText(_translate("OptionsGroup", "TextLabel", None))
        self.label_5.setText(_translate("OptionsGroup", "Zoom", None))
        self.chkLimitNrOfTiles.setText(_translate("OptionsGroup", "Limit the number of loaded tiles", None))
        self.chkMergeTiles.setText(_translate("OptionsGroup", "Merge Tiles (slow)", None))

