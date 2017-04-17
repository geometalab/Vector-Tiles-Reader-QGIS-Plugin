# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'dlg_file_connection.ui'
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

class Ui_DlgFileConnection(object):
    def setupUi(self, DlgFileConnection):
        DlgFileConnection.setObjectName(_fromUtf8("DlgFileConnection"))
        DlgFileConnection.setWindowModality(QtCore.Qt.WindowModal)
        DlgFileConnection.resize(690, 323)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(DlgFileConnection.sizePolicy().hasHeightForWidth())
        DlgFileConnection.setSizePolicy(sizePolicy)
        DlgFileConnection.setMinimumSize(QtCore.QSize(0, 0))
        DlgFileConnection.setSizeGripEnabled(False)
        DlgFileConnection.setModal(True)
        self.gridLayout_4 = QtGui.QGridLayout(DlgFileConnection)
        self.gridLayout_4.setObjectName(_fromUtf8("gridLayout_4"))
        self.grpOptions = QtGui.QGroupBox(DlgFileConnection)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.grpOptions.sizePolicy().hasHeightForWidth())
        self.grpOptions.setSizePolicy(sizePolicy)
        self.grpOptions.setMinimumSize(QtCore.QSize(0, 190))
        self.grpOptions.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.grpOptions.setObjectName(_fromUtf8("grpOptions"))
        self.gridLayout_4.addWidget(self.grpOptions, 1, 0, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.btnOpen = QtGui.QPushButton(DlgFileConnection)
        self.btnOpen.setEnabled(False)
        self.btnOpen.setCheckable(False)
        self.btnOpen.setDefault(False)
        self.btnOpen.setFlat(False)
        self.btnOpen.setObjectName(_fromUtf8("btnOpen"))
        self.horizontalLayout_2.addWidget(self.btnOpen)
        self.btnCancel = QtGui.QPushButton(DlgFileConnection)
        self.btnCancel.setObjectName(_fromUtf8("btnCancel"))
        self.horizontalLayout_2.addWidget(self.btnCancel)
        self.gridLayout_4.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)
        self.groupBox = QtGui.QGroupBox(DlgFileConnection)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox.sizePolicy().hasHeightForWidth())
        self.groupBox.setSizePolicy(sizePolicy)
        self.groupBox.setMinimumSize(QtCore.QSize(0, 0))
        self.groupBox.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.groupBox.setSizeIncrement(QtCore.QSize(0, 0))
        self.groupBox.setObjectName(_fromUtf8("groupBox"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.groupBox)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.btnBrowse = QtGui.QPushButton(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnBrowse.sizePolicy().hasHeightForWidth())
        self.btnBrowse.setSizePolicy(sizePolicy)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/plugins/vectortilereader/folder.svg")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btnBrowse.setIcon(icon)
        self.btnBrowse.setObjectName(_fromUtf8("btnBrowse"))
        self.gridLayout.addWidget(self.btnBrowse, 0, 2, 1, 1, QtCore.Qt.AlignVCenter)
        self.lblError = QtGui.QLabel(self.groupBox)
        self.lblError.setStyleSheet(_fromUtf8("color: rgb(255, 0, 0);"))
        self.lblError.setScaledContents(False)
        self.lblError.setWordWrap(True)
        self.lblError.setIndent(-1)
        self.lblError.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextSelectableByMouse)
        self.lblError.setObjectName(_fromUtf8("lblError"))
        self.gridLayout.addWidget(self.lblError, 1, 1, 1, 2, QtCore.Qt.AlignTop)
        self.txtPath = QtGui.QLineEdit(self.groupBox)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtPath.sizePolicy().hasHeightForWidth())
        self.txtPath.setSizePolicy(sizePolicy)
        self.txtPath.setMinimumSize(QtCore.QSize(20, 0))
        self.txtPath.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.txtPath.setObjectName(_fromUtf8("txtPath"))
        self.gridLayout.addWidget(self.txtPath, 0, 1, 1, 1, QtCore.Qt.AlignVCenter)
        self.label_2 = QtGui.QLabel(self.groupBox)
        self.label_2.setMinimumSize(QtCore.QSize(40, 0))
        self.label_2.setMaximumSize(QtCore.QSize(16777215, 20))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 0, 0, 1, 1)
        self.horizontalLayout_3.addLayout(self.gridLayout)
        self.gridLayout_4.addWidget(self.groupBox, 0, 0, 1, 1)

        self.retranslateUi(DlgFileConnection)
        QtCore.QObject.connect(self.btnCancel, QtCore.SIGNAL(_fromUtf8("clicked()")), DlgFileConnection.reject)
        QtCore.QMetaObject.connectSlotsByName(DlgFileConnection)

    def retranslateUi(self, DlgFileConnection):
        DlgFileConnection.setWindowTitle(_translate("DlgFileConnection", "Add Vector Tile Layer", None))
        self.grpOptions.setTitle(_translate("DlgFileConnection", "Options", None))
        self.btnOpen.setText(_translate("DlgFileConnection", "Open", None))
        self.btnCancel.setText(_translate("DlgFileConnection", "Cancel", None))
        self.groupBox.setTitle(_translate("DlgFileConnection", "Source", None))
        self.btnBrowse.setText(_translate("DlgFileConnection", "Browse", None))
        self.lblError.setText(_translate("DlgFileConnection", "Show any errors here", None))
        self.label_2.setText(_translate("DlgFileConnection", "Source", None))

import resources_rc
