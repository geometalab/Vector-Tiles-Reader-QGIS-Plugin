
class VectorTile:
    
    decoded_data = None

    def __init__(self, zoom_level, x, y):
        self.zoom_level = zoom_level
        self.column = x
        self.row = y
    
    def __str__(self):
        return "Tile (zoom={}, col={}, row={}".format(self.zoom_level, self.column, self.row)
