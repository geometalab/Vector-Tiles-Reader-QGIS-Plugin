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

    def merge_features(self, layer):
        layer_name = layer.name()

        info("Merging features of layer: {}".format(layer_name))

        self._prepare_features_for_dissolvment(layer)
        dissolved_layer = self._dissolve(layer)

        return dissolved_layer

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
        debug('Dissolvement complete: {}', layer.name())
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

    @staticmethod
    def _dissolve(layer):
        debug("Dissolving layer")
        target_file = FileHelper.get_unique_file_name()
        processing.runalg("qgis:dissolve", layer, False, "dissolveGroup", target_file)
        dissolved_layer = QgsVectorLayer(target_file, "Dissolved", "ogr")
        return dissolved_layer
