# from qgis.analysis import QgsOverlayAnalyzer
from qgis.core import QgsMapLayerRegistry, QgsField
from PyQt4.QtCore import QVariant
import processing


class FeatureMerger:

    def __init__(self):
        print "init feature merger"

    def merge_features(self, layer, group):
        print "now merging features of layer: ", layer.name()
        intersection_layer = self._create_intersection_layer(layer)
        join_layer = self._join_by_attribute(intersection_layer)
        self._create_new_featurenr_attribute(join_layer)
        self._dissolve(join_layer)

    def _create_intersection_layer(self, layer):
        processing.runandload("qgis:intersection", layer, layer, True, "memory:temp_layer")
        intersection_layer = QgsMapLayerRegistry.instance().mapLayersByName("Intersection")[0]
        return intersection_layer

    def _join_by_attribute(self, layer):
        print("create join layer")
        processing.runandload("qgis:joinattributesbylocation", layer, layer, u'intersects', 0, 1, "min,max", 1, 'memory:temp_layer')
        joined_layer = QgsMapLayerRegistry.instance().mapLayersByName("Joined layer")[0]
        return joined_layer

    def _create_new_featurenr_attribute(self, layer):
        field = QgsField('newFeatureNr', QVariant.String)
        layer.addExpressionField("concat(\"minfeatureNr\", \"maxfeatureNr\") ", field)

    def _dissolve(self, layer):
        processing.runandload("qgis:dissolve", layer, False, "newFeatureNr", "memory:temp_layer")