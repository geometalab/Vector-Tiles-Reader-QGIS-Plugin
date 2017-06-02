from file_helper import FileHelper
import json


class VtWriter:

    def __init__(self, iface, file_destination):
        self.iface = iface
        self.file_destination = file_destination

    def export(self):
        tile_names = self._get_loaded_tile_names()
        tiles = self._load_tiles(tile_names)

    def _get_loaded_tile_names(self):
        all_layers = self.iface.legendInterface().layers()
        tile_names = set()
        for l in all_layers:
            layer_source = l.source()
            if layer_source.startswith(FileHelper.get_temp_dir()):
                with open(layer_source, "r") as f:
                    feature_collection = json.load(f)
                    source_name = feature_collection["source"]
                    zoom_level = feature_collection["zoom_level"]
                    collection_tiles = map(lambda t: (int(t.split(";")[0]), int(t.split(";")[1])), feature_collection["tiles"])
                    for t in collection_tiles:
                        cached_tile_name = FileHelper.get_cached_tile_file_name(source_name, zoom_level, t[0], t[1])
                        tile_names.add(cached_tile_name)
        return tile_names

    def _load_tiles(self, tile_names):
        tiles = []
        for name in tile_names:
            tile = FileHelper.get_cached_tile(name)
            if tile:
                tiles.append(tile)
        return tiles
