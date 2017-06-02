from file_helper import FileHelper
import json


class VtWriter:

    def __init__(self, iface, file_destination):
        self.iface = iface
        self.file_destination = file_destination

    def export(self):
        tiles = self._get_loaded_tiles()

    def _get_loaded_tiles(self):
        all_layers = self.iface.legendInterface().layers()
        tiles = set()
        for l in all_layers:
            layer_source = l.source()
            if layer_source.startswith(FileHelper.get_temp_dir()):
                with open(layer_source, "r") as f:
                    feature_collection = json.load(f)
                    collection_tiles = map(lambda t: (int(t.split(";")[0]), int(t.split(";")[1])), feature_collection["tiles"])
                    for t in collection_tiles:
                        tiles.add(t)
        print tiles
