import mapbox_vector_tile
from cStringIO import StringIO
from gzip import GzipFile
from file_helper import FileHelper


def decode_tile(tile_data_tuple):
    tile = tile_data_tuple[0]
    if not tile.decoded_data:
        encoded_data = tile_data_tuple[1]
        tile.decoded_data = _decode_binary_tile_data(encoded_data)
    return tile


def _decode_binary_tile_data(encoded_data):
    """
     * Decodes the (gzipped) PBF that has been read from the tile source.
    :param encoded_data:
    :return:
    """
    decoded_data = None
    if encoded_data:
        try:
            is_gzipped = FileHelper.is_gzipped(encoded_data)
            # is_gzipped = True
            if is_gzipped:
                # file_content = GzipFile('', 'r', 0, StringIO(encoded_data)).read()
                file_content = GzipFile(StringIO(encoded_data)).read()
            else:
                file_content = encoded_data
            decoded_data = mapbox_vector_tile.decode(file_content)
        except:
            pass
    else:
        decoded_data = None
    return decoded_data
