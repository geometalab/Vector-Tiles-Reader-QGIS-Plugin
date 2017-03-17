from qgis.core import QgsMapLayerRegistry, QgsField, QgsVectorLayer, QgsFeatureRequest, QgsSpatialIndex
from PyQt4.QtCore import QVariant
from file_helper import FileHelper
from log_helper import info, warn, critical, debug
import processing
import uuid


class FeatureMerger:
    """
     * The class FeatureMerger can be used to merge features over tile boundaries.
    """

    def __init__(self):
        pass

    def merge_features(self, layer, remove_invalid_features=False):

        # return layer, None

        layer_name = layer.name()
        # todo: remove after testing
        if layer_name.split("_")[0] not in ["forest", "lake"]:
            return layer, None

        info("Merging features of layer '{}'".format(layer_name))

        # valid_layer, invalid_layer = self._validate_layer(layer)
        #
        # invalid_feature_ids = invalid_layer.allFeatureIds()
        # nr_invalid_features = len(invalid_feature_ids)
        # debug("Nr. invalid features: {}".format(nr_invalid_features))

        # if nr_invalid_features > 0:
        #     if remove_invalid_features:
        #         return layer, invalid_layer
        #     else:
        #         debug("This file contains features, that cannot be fixed: {}".format(invalid_layer.source()))
        #         valid_layer = layer

        self._prepare_features_for_dissolvment(layer)
        dissolved_layer = self._dissolve(layer)

        return dissolved_layer, None

    # @staticmethod
    # def _validate_layer(layer):
    #     """
    #      * Validates the layer and removes all invalid geometries.
    #     :param layer:
    #     :return:
    #     """
    #     debug("Validating layer")
    #     target_file_valid = FileHelper.get_unique_file_name()
    #     target_file_invalid = FileHelper.get_unique_file_name()
    #     processing.runalg("qgis:checkvalidity", layer, 2, target_file_valid, target_file_invalid, None)
    #     valid_layer = QgsVectorLayer(target_file_valid, "Valid", "ogr")
    #     invalid_layer = QgsVectorLayer(target_file_invalid, "Invalid", "ogr")
    #     return valid_layer, invalid_layer

    # @staticmethod
    # def _create_intersection_layer(layer):
    #     debug("Intersecting layer")
    #     target_file = FileHelper.get_unique_file_name()
    #     processing.runalg("qgis:intersection", layer, layer, True, target_file)
    #     intersection_layer = QgsVectorLayer(target_file, "Intersection", "ogr")
    #     return intersection_layer

    @staticmethod
    def _prepare_features_for_dissolvment(layer):
        _DISSOLVE_GROUP_FIELD = "dissolveGroup"
        layer.startEditing()
        layer.dataProvider().addAttributes([QgsField(_DISSOLVE_GROUP_FIELD, QVariant.String, len=36)])
        layer.updateFields()
        # Create a dictionary of all features
        feature_dict = {f.id(): f for f in layer.getFeatures()}

        # Build a spatial index
        index = QgsSpatialIndex()
        for f in feature_dict.values():
            index.insertFeature(f)

        for f in feature_dict.values():
            if f[_DISSOLVE_GROUP_FIELD]:
                continue
            f[_DISSOLVE_GROUP_FIELD] = str(uuid.uuid4())
            FeatureMerger._assign_dissolve_group_to_neighbours_rec(_DISSOLVE_GROUP_FIELD, index, f, [], feature_dict, feature_handler=lambda feat: layer.updateFeature(feat))
            layer.updateFeature(f)
        layer.commitChanges()
        print 'Processing complete.'
        return

    @staticmethod
    def _assign_dissolve_group_to_neighbours_rec(dissolve_gorup_field, index, f, neighbours, feature_dict, feature_handler):
        geom = f.geometry()

        if geom:
            intersecting_ids = index.intersects(geom.boundingBox())
        else:
            intersecting_ids = []

        new_neighbours = []
        for intersecting_id in intersecting_ids:
            intersecting_f = feature_dict[intersecting_id]
            if f != intersecting_f and not intersecting_f.geometry().disjoint(geom):
                if not intersecting_f[dissolve_gorup_field]:
                    intersecting_f[dissolve_gorup_field] = f[dissolve_gorup_field]
                    new_neighbours.append(intersecting_f)
                    feature_handler(intersecting_f)

        for n in new_neighbours:
            FeatureMerger._assign_dissolve_group_to_neighbours_rec(dissolve_gorup_field, index, n, neighbours, feature_dict, feature_handler)

        neighbours.extend(new_neighbours)
        return neighbours

    # @staticmethod
    # def _get_layer(name):
    #     result = None
    #     layers = QgsMapLayerRegistry.instance().mapLayersByName(name)
    #     if len(layers) > 0:
    #         result = layers[0]
    #     return result

    @staticmethod
    def _dissolve(layer):
        debug("Dissolving layer")
        target_file = FileHelper.get_unique_file_name()
        processing.runalg("qgis:dissolve", layer, False, "dissolveGroup", target_file)
        dissolved_layer = QgsVectorLayer(target_file, "Dissolved", "ogr")
        return dissolved_layer
