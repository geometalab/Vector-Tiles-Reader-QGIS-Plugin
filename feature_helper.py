from qgis.core import QgsMapLayerRegistry, QgsField, QgsVectorLayer, QgsFeatureRequest
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

    def merge_features(self, layer, remove_invalid_features=False):

        layer_name = layer.name()

        if layer_name != "lake_Polygon":
            return layer, None

        info("Merging features of layer '{}'".format(layer_name))

        valid_layer, invalid_layer = self._validate_layer(layer)

        nr_invalid_features = len(invalid_layer.allFeatureIds())
        debug("Nr. invalid features: {}".format(nr_invalid_features))

        if remove_invalid_features and nr_invalid_features > 0:
            return layer, invalid_layer

        if not remove_invalid_features or nr_invalid_features == 0:
            valid_layer = layer

        intersection_layer = None
        if valid_layer:
            intersection_layer = self._create_intersection_layer(valid_layer)

        join_layer = None
        if intersection_layer:
            join_layer = self._join_by_attribute(intersection_layer)
        else:
            print("Intersection layer not found")

        dissolved_layer = None
        if join_layer:
            self._create_new_featurenr_attribute(join_layer)
            dissolved_layer = self._dissolve(join_layer)
        else:
            print("Join layer not found")
        return dissolved_layer, None

    @staticmethod
    def _validate_layer(layer):
        """
         * Validates the layer and removes all invalid geometries.
        :param layer:
        :return:
        """
        debug("Validating layer")
        target_file_valid = FileHelper.get_unique_file_name()
        target_file_invalid = FileHelper.get_unique_file_name()
        processing.runalg("qgis:checkvalidity", layer, 2, target_file_valid, target_file_invalid, None)
        valid_layer = QgsVectorLayer(target_file_valid, "Valid", "ogr")
        invalid_layer = QgsVectorLayer(target_file_invalid, "Invalid", "ogr")
        return valid_layer, invalid_layer

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
