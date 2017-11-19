try:
    from qgis.core import (
        QgsMapLayerRegistry
    )
except ImportError:
    from qgis.core import (
        QgsProject as QgsMapLayerRegistry
    )

from qgis.core import (
        QgsApplication,
        QgsPoint,
        QgsRectangle,
        QgsCoordinateReferenceSystem,
        QgsProject,
        QgsCoordinateReferenceSystem,
        QgsCoordinateTransform,
        QgsPoint
    )
from qgis.gui import QgsMessageBar

try:
    from PyQt4.QtCore import QSettings, QTimer, Qt, pyqtSlot, pyqtSignal, QObject
    from PyQt4.QtGui import *
    from ..ui import resources_rc_qt4
except ImportError:
    from PyQt5.QtCore import QSettings, QTimer, Qt, pyqtSlot, pyqtSignal, QObject
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from ..ui import resources_rc_qt5
