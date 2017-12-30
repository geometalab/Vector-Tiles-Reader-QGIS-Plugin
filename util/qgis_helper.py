from .vtr_2to3 import *


def get_loaded_layers_of_connection(connection_name):
    layers = []
    for l in list(QgsMapLayerRegistry.instance().mapLayers().values()):
        layer_source = l.customProperty("VectorTilesReader/vector_tile_source")
        if layer_source and connection_name == layer_source:
            layers.append(l)
    return layers