from qgis.core import QgsMapLayerRegistry, QgsField, QgsVectorLayer, QgsFeatureRequest, QgsSpatialIndex
from PyQt4.QtCore import QVariant
from file_helper import FileHelper
from log_helper import info, warn, critical, debug
import processing
import uuid
import numbers


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

        idx = layer.fieldNameIndex('class')

        # Build a spatial index
        index = QgsSpatialIndex()
        for f in feature_dict.values():
            index.insertFeature(f)

        for f in feature_dict.values():
            if f[_DISSOLVE_GROUP_FIELD]:
                continue
            f[_DISSOLVE_GROUP_FIELD] = str(uuid.uuid4())
            FeatureMerger._assign_dissolve_group_to_neighbours_rec(_DISSOLVE_GROUP_FIELD, index, f, [], feature_dict, feature_handler=lambda feat: layer.updateFeature(feat), feature_class_attr_index=idx)
            layer.updateFeature(f)
        layer.commitChanges()
        debug('Dissolvement complete: {}', layer.name())
        return

    @staticmethod
    def _assign_dissolve_group_to_neighbours_rec(dissolve_gorup_field, index, f, neighbours, feature_dict, feature_handler, feature_class_attr_index):
        geom = f.geometry()

        if geom:
            intersecting_ids = index.intersects(geom.boundingBox())
        else:
            intersecting_ids = []

        new_neighbours = []
        for intersecting_id in intersecting_ids:
            intersecting_f = feature_dict[intersecting_id]
            if f != intersecting_f and not intersecting_f.geometry().disjoint(geom) and f.attributes()[feature_class_attr_index] == intersecting_f.attributes()[feature_class_attr_index]:
                if not intersecting_f[dissolve_gorup_field]:
                    intersecting_f[dissolve_gorup_field] = f[dissolve_gorup_field]
                    new_neighbours.append(intersecting_f)
                    feature_handler(intersecting_f)

        for n in new_neighbours:
            FeatureMerger._assign_dissolve_group_to_neighbours_rec(dissolve_gorup_field, index, n, neighbours, feature_dict, feature_handler, feature_class_attr_index)

        neighbours.extend(new_neighbours)
        return neighbours

    @staticmethod
    def _dissolve(layer):
        debug("Dissolving layer")
        target_file = FileHelper.get_unique_geojson_file_name()
        processing.runalg("qgis:dissolve", layer, False, "dissolveGroup", target_file)
        dissolved_layer = QgsVectorLayer(target_file, "Dissolved", "ogr")
        return dissolved_layer


class _GeoTypes:
    def __init__(self):
        pass

    POINT = "Point"
    LINE_STRING = "LineString"
    POLYGON = "Polygon"

GeoTypes = _GeoTypes()

geo_types = {
    1: GeoTypes.POINT,
    2: GeoTypes.LINE_STRING,
    3: GeoTypes.POLYGON}


def is_multi(geo_type, coordinates):
    """
    * Returns true, if the specified coordinates belong to a Multi geometry (e.g. MultiPolygon or MultiLineString)
    :param geo_type:
    :param coordinates:
    :return:
    """

    if geo_type == GeoTypes.POINT:
        is_single = len(coordinates) == 2 and all(isinstance(c, int) for c in coordinates)
        return not is_single
    elif geo_type == GeoTypes.LINE_STRING:
        is_array_of_tuples = all(len(c) == 2 and all(isinstance(ci, int) for ci in c) for c in coordinates)
        is_single = is_array_of_tuples
        return not is_single
    elif geo_type == GeoTypes.POLYGON:
        return get_array_depth(coordinates, 0) >= 2
    return False


def get_array_depth(arr, depth):
    """
    * Returns the depth of an array.
      >> Example: arr=[1,2,3], depth=0, then the resulting depth will be 0
      >> Example: arr=[[1,2], [3,4]], depth=0, then the resulting depth will be 1
    :param arr:
    :param depth:
    :return:
    """

    if all(isinstance(c, numbers.Real) for c in arr[0]):
        return depth
    else:
        depth += 1
        return get_array_depth(arr[0], depth)


def map_coordinates_recursive(coordinates, tile_extent, mapper_func, all_out_of_bounds_func=None):
    """
    Recursively traverses the array of coordinates (depth first) and applies the specified function
    """
    any_tuples_inside_bounds = False
    tuple_count_on_current_array_depth = 0
    tmp = []
    is_coordinate_tuple = len(coordinates) == 2 and all(isinstance(c, int) for c in coordinates)
    if is_coordinate_tuple:
        newval = mapper_func(coordinates)
        tmp.append(newval)
    else:
        for coord in coordinates:
            is_coordinate_tuple = len(coord) == 2 and all(isinstance(c, int) for c in coord)
            if is_coordinate_tuple:
                tuple_count_on_current_array_depth += 1
                if not any_tuples_inside_bounds and 1 <= coord[0] <= tile_extent and 1 <= coord[1] <= tile_extent:
                    any_tuples_inside_bounds = True

                newval = mapper_func(coord)
                tmp.append(newval)
            else:
                tmp.append(map_coordinates_recursive(coordinates=coord,
                                                     tile_extent=tile_extent,
                                                     mapper_func=mapper_func,
                                                     all_out_of_bounds_func=all_out_of_bounds_func))

    all_out_of_bounds = tuple_count_on_current_array_depth > 0 and not any_tuples_inside_bounds
    if all_out_of_bounds_func:
        all_out_of_bounds_func(all_out_of_bounds)
    return tmp
