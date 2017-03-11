# from qgis.analysis import QgsOverlayAnalyzer
from qgis.core import QgsMapLayerRegistry
import processing


class FeatureMerger:

    def __init__(self):
        print "init feature merger"

    def merge_features(self, layer, group):
        print "now merging features of layer: ", layer.name()
        processing.runandload("qgis:intersection", layer, layer, True, "memory:temp_layer")
        intersection_layer = QgsMapLayerRegistry.instance().mapLayersByName("Intersection")[0]


    # def _join_attributes(self, layer):
        # processing.runalg("qgis:joinattributesbylocation","BKMapPLUTO.shp","DCP_nyc_freshzoning.shp","['intersects']",0,"sum,mean,min,max,median",0,'result.shp')
