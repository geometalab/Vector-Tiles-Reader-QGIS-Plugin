from qgis.core import QgsMapLayerRegistry, QgsField, QgsVectorLayer
from PyQt4.QtCore import QVariant
import processing
from file_helper import FileHelper


class FeatureMerger:

    def __init__(self):
        pass

    def merge_features(self, layer):
        join_layer = None
        dissolved_layer = None
        layer_name = layer.name()
        print "now merging features of layer: ", layer_name
        intersection_layer = self._create_intersection_layer(layer)
        if intersection_layer:
            join_layer = self._join_by_attribute(intersection_layer)
        else:
            print("Intersection layer not found")

        if join_layer:
            self._create_new_featurenr_attribute(join_layer)
            dissolved_layer = self._dissolve(join_layer)
        else:
            print("Join layer not found")
        return dissolved_layer

    @staticmethod
    def _create_intersection_layer(layer):
        target_file = FileHelper.get_unique_file_name("shp")
        processing.runalg("qgis:intersection", layer, layer, True, target_file)
        intersection_layer = QgsVectorLayer(target_file, "Intersection", "ogr")
        return intersection_layer

    @staticmethod
    def _join_by_attribute(layer):
        target_file = FileHelper.get_unique_file_name("shp")
        processing.runalg("qgis:joinattributesbylocation", layer, layer, u'intersects', 0, 1, "min,max", 1, target_file)
        joined_layer = QgsVectorLayer(target_file, "Joined Layer", "ogr")
        return joined_layer

    @staticmethod
    def _get_layer(name):
        result = None
        layers = QgsMapLayerRegistry.instance().mapLayersByName(name)
        if len(layers) > 0:
            result = layers[0]
        return result

    @staticmethod
    def _create_new_featurenr_attribute(layer):
        field = QgsField('newFeatureNr', QVariant.String)
        layer.addExpressionField("concat(\"minfeatureNr\", \"maxfeatureNr\") ", field)

    @staticmethod
    def _dissolve(layer):
        target_file = FileHelper.get_unique_file_name("shp")
        processing.runalg("qgis:dissolve", layer, False, "newFeatureNr", target_file)
        dissolved_layer = QgsVectorLayer(target_file, "Dissolved", "ogr")
        return dissolved_layer
