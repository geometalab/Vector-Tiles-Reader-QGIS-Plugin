from qgis.core import *
from qgis.gui import *

from PyQt4 import QtCore, QtGui, QtTest

import unittest

QgsApplication.setPrefixPath("/usr/local", True)

QgsApplication.initQgis()

if len(QgsProviderRegistry.instance().providerList()) == 0:
    raise RuntimeError('No data providers available.')

QgsApplication.exitQgis()