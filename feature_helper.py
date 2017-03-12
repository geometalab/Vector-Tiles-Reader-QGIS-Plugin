from qgis.core import QgsMapLayerRegistry, QgsField, QgsVectorLayer
from PyQt4.QtCore import QVariant
import processing
from file_helper import FileHelper
from log_helper import info, warn, critical, debug


class FeatureMerger:
    """
     * The class FeatureMerger can be used to merge features over tile boundaries.
    """

    def __init__(self):
        pass

    def merge_features(self, layer):
        join_layer = None
        dissolved_layer = None
        intersection_layer = None
        layer_name = layer.name()
        info("Merging features of layer '{}'".format(layer_name))
        # print "now merging features of layer: ", layer_name

        # cleaned_layer = self._clean_layer(layer)
        validated_layer = self._validate_layer(layer)

        if validated_layer:
            intersection_layer = self._create_intersection_layer(validated_layer)

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
    def _validate_layer(layer):
        """
         * Validates the layer and removes all invalid geometries.
        :param layer:
        :return:
        """
        debug("Validating layer")
        target_file = FileHelper.get_unique_file_name()
        processing.runalg("qgis:checkvalidity", layer, 2, target_file, None, None)
        valid_layer = QgsVectorLayer(target_file, "Valid", "ogr")
        return valid_layer

    @staticmethod
    def _clean_layer(layer):
        """
         * Uses the grass7:v.clean algorithm to clean invalid geometries. Due to a bug in qgis this it not working at the moment (https://hub.qgis.org/issues/16195)
         * The workaround for this problem is by validating the layer. However, validating just removes the invalid geometries instead of fixing them.
        :param layer:
        :return:
        """
        debug("Cleaning layer")
        target_file = FileHelper.get_unique_file_name()
        print("Executing grass clean")
        processing.runalg("grass7:v.clean", layer, 0, 0.1, None, -1, 0.0001, target_file, None)
        cleaned_layer = QgsVectorLayer(target_file, "Cleaned", "ogr")
        return cleaned_layer

    @staticmethod
    def _create_intersection_layer(layer):
        debug("Intersecting layer")
        target_file = FileHelper.get_unique_file_name()
        processing.runalg("qgis:intersection", layer, layer, True, target_file)
        intersection_layer = QgsVectorLayer(target_file, "Intersection", "ogr")
        return intersection_layer

    @staticmethod
    def _join_by_attribute(layer):
        debug("Joining layer")
        target_file = FileHelper.get_unique_file_name()
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
        debug("Add calculated property to layer")
        field = QgsField('newFeatureNr', QVariant.String)
        layer.addExpressionField("concat(\"minfeatureNr\", \"maxfeatureNr\") ", field)

    @staticmethod
    def _dissolve(layer):
        debug("Dissolving layer")
        target_file = FileHelper.get_unique_file_name()
        processing.runalg("qgis:dissolve", layer, False, "newFeatureNr", target_file)
        dissolved_layer = QgsVectorLayer(target_file, "Dissolved", "ogr")
        return dissolved_layer
