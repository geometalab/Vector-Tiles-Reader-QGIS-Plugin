
class VectorTile:
    
    def __init__(self, zoom_level, x, y, decoded_data):
        self.zoom_level = zoom_level
        self.column = x
        self.row = y
        self.decoded_data = decoded_data
    
    def __str__(self):
        return "Tile (zoom={}, col={}, row={}".format(self.zoom_level, self.column, self.row)
