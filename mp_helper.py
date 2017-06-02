import mapbox_vector_tile


def decode_tile(tile_data_tuple):
    tile = tile_data_tuple[0]
    if not tile.decoded_data:
        encoded_data = tile_data_tuple[1]
        tile.decoded_data = mapbox_vector_tile.decode(encoded_data)
    return tile
