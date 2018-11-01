try:
    from qgis.core import (
        QgsMapLayerRegistry,
        QgsPoint
    )
except ImportError:
    from qgis.core import (
        QgsProject as QgsMapLayerRegistry,
        QgsPointXY as QgsPoint
    )

from qgis.core import (
    QgsApplication,
    QgsRectangle,
    QgsCoordinateReferenceSystem,
    QgsProject,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsField,
    QgsVectorLayer,
    QgsFeatureRequest,
    QgsSpatialIndex,
    QgsGeometry,
    QgsNetworkAccessManager
    )

import os
try:
    from PyQt4.QtCore import *
    from PyQt4.QtGui import *
    from PyQt4.QtNetwork import *
    if "VTR_TESTS" not in os.environ or os.environ["VTR_TESTS"] != '1':
        from ..ui import resources_rc_qt4
    QGIS3 = False
except ImportError:
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *
    from PyQt5.QtNetwork import *
    if "VTR_TESTS" not in os.environ or os.environ["VTR_TESTS"] != '1':
        from ..ui import resources_rc_qt5
    QGIS3 = True
