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
        #
        layer_name = layer.name()
        if layer_name not in ["forest_8", "forest_14", "forest", "forest_14", "lake_14", "lake"]:
            return layer, None

        info("Merging features of layer '{}'".format(layer_name))

        valid_layer, invalid_layer = self._validate_layer(layer)

        nr_invalid_features = len(invalid_layer.allFeatureIds())
        debug("Nr. invalid features: {}".format(nr_invalid_features))

        if remove_invalid_features and nr_invalid_features > 0:
            return layer, invalid_layer

        # if not remove_invalid_features or nr_invalid_features == 0:
        #     valid_layer = layer

        if not remove_invalid_features and nr_invalid_features > 0:
            debug("There are still invalid geometries! Why is that?")

        intersection_layer = None
        if valid_layer:
            intersection_layer = self._create_intersection_layer(valid_layer)

        dissolved_layer = None
        if intersection_layer:
            self._prepare_features_for_dissolvment(intersection_layer)
            dissolved_layer = self._dissolve(intersection_layer)
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
    def _prepare_features_for_dissolvment(layer):
        _NEW_NEIGHBORS_FIELD = 'NEIGHBORS'
        _NEW_SUM_FIELD = 'SUM'
        _DISSOLVE_GROUP_FIELD = "dissolveGroup"
        # Create 2 new fields in the layer that will hold the list of neighbors and sum
        # of the chosen field.
        layer.startEditing()
        layer.dataProvider().addAttributes(
            [QgsField(_NEW_NEIGHBORS_FIELD, QVariant.String),
             QgsField(_NEW_SUM_FIELD, QVariant.Int),
             QgsField(_DISSOLVE_GROUP_FIELD, QVariant.String, len=36)])
        layer.updateFields()
        # Create a dictionary of all features
        feature_dict = {f.id(): f for f in layer.getFeatures()}

        # Build a spatial index
        index = QgsSpatialIndex()
        for f in feature_dict.values():
            index.insertFeature(f)

        for f in feature_dict.values():
            if f["dissolveGroup"]:
                continue
            f[_DISSOLVE_GROUP_FIELD] = str(uuid.uuid4())
            FeatureMerger._assign_dissolve_group_to_neighbours_rec(index, f, [], feature_dict, feature_handler=lambda feat: layer.updateFeature(feat))
            layer.updateFeature(f)
        layer.commitChanges()
        print 'Processing complete.'
        return

    @staticmethod
    def _assign_dissolve_group_to_neighbours_rec(index, f, neighbours, feature_dict, feature_handler):
        geom = f.geometry()

        if geom:
            intersecting_ids = index.intersects(geom.boundingBox())
        else:
            intersecting_ids = []

        new_neighbours = []
        for intersecting_id in intersecting_ids:
            intersecting_f = feature_dict[intersecting_id]
            if f != intersecting_f and not intersecting_f.geometry().disjoint(geom):
                if not intersecting_f["dissolveGroup"]:
                    intersecting_f["dissolveGroup"] = f["dissolveGroup"]
                    new_neighbours.append(intersecting_f)
                    feature_handler(intersecting_f)

        for n in new_neighbours:
            FeatureMerger._assign_dissolve_group_to_neighbours_rec(index, n, neighbours, feature_dict, feature_handler)

        neighbours.extend(new_neighbours)
        return neighbours

    @staticmethod
    def _get_layer(name):
        result = None
        layers = QgsMapLayerRegistry.instance().mapLayersByName(name)
        if len(layers) > 0:
            result = layers[0]
        return result

    @staticmethod
    def _dissolve(layer):
        debug("Dissolving layer")
        target_file = FileHelper.get_unique_file_name()
        processing.runalg("qgis:dissolve", layer, False, "dissolveGroup", target_file)
        dissolved_layer = QgsVectorLayer(target_file, "Dissolved", "ogr")
        return dissolved_layer
