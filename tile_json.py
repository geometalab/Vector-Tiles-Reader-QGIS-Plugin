import sys
import urllib2
import json
from log_helper import critical, debug

class TileJSON:
    """
     * Helper class to process a TileJSON url v2.2.0
     * https://github.com/mapbox/tilejson-spec/tree/master/2.2.0
    """
    def __init__(self, url):
        self.url = url
        self.json = None

    def load(self):
        success = False
        try:
            response = urllib2.urlopen(self.url)
            data = response.read()
            self.json = json.loads(data)
            debug("TileJSON loaded: {}", self.json)
            success = True
        except urllib2.HTTPError as e:
            critical("HTTP error {}: {}", e.code, e.message)
        except:
            critical("Loading TileJSON failed ({}): {}", self.url, sys.exc_info())
        return success

    def vector_layers(self):
        layers = []
        if self.json and "vector_layers" in self.json:
            for l in self.json["vector_layers"]:
                debug("Layer: {}", l)
