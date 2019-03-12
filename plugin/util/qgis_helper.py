from typing import List

from qgis.core import QgsProject, QgsVectorLayer


def get_loaded_layers_of_connection(connection_name: str) -> List[QgsVectorLayer]:
    layers = []
    for l in list(QgsProject.instance().mapLayers().values()):
        layer_source = l.customProperty("VectorTilesReader/vector_tile_source")
        if layer_source and connection_name == layer_source:
            layers.append(l)
    return layers
