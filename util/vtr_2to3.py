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
    QgsPoint,
    QgsPointXY,
    QgsField,
    QgsVectorLayer,
    QgsFeatureRequest,
    QgsSpatialIndex,
    QgsGeometry,
    QgsNetworkAccessManager
    )
from qgis.gui import QgsMessageBar

try:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    from PyQt4.QtNetwork import *
    from ..ui import resources_rc_qt4
except ImportError:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtNetwork import *
    from ..ui import resources_rc_qt5
