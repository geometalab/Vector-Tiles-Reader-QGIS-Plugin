import os
import sys
from ctypes import c_bool, c_char_p, c_double, c_uint16, c_void_p, cast, cdll

import mapbox_vector_tile

from .file_helper import get_plugin_directory
from .log_helper import info, warn

try:
    import simplejson as json
except ImportError:
    import json


def decode_tile_python(tile_data_clip):
    tile = tile_data_clip[0]
    encoded_data = tile_data_clip[1]
    # clip_tile = tile_data_clip[2]

    decoded_data = None
    if encoded_data and not tile.decoded_data:
        decoded_data = mapbox_vector_tile.decode(encoded_data)
    return tile, decoded_data


def get_lib_for_current_platform():
    is_64_bit = sys.maxsize > 2 ** 32
    if is_64_bit:
        bitness_string = "x86_64"
    else:
        bitness_string = "i686"
    lib = None
    if sys.platform.startswith("linux"):
        lib = "pbf2geojson_linux_{}.so".format(bitness_string)
    elif sys.platform.startswith("win32"):
        lib = "pbf2geojson_windows_{}.dll".format(bitness_string)
    elif sys.platform.startswith("darwin"):
        lib = "pbf2geojson_osx_{}.so".format(bitness_string)
    if lib:
        # lib = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "ext-libs", "pbf2geojson", lib)
        lib = os.path.join(os.path.abspath(get_plugin_directory()), "ext-libs", "pbf2geojson", lib)
    return lib


def load_lib():
    lib = None
    path = get_lib_for_current_platform()
    if path and os.path.isfile(path):
        try:
            lib = cdll.LoadLibrary(path)
            lib.decodeMvtToJson.argtypes = [
                c_bool,
                c_uint16,
                c_uint16,
                c_uint16,
                c_double,
                c_double,
                c_double,
                c_double,
                c_char_p,
            ]
            lib.decodeMvtToJson.restype = c_void_p
            lib.freeme.argtypes = [c_void_p]
            lib.freeme.restype = None
        except:
            warn("Loading lib failed for platform '{}': {}, {}", sys.platform, path, sys.exc_info()[1])
    else:
        warn("No prebuilt binary found for: {}, 64bit={}", sys.platform, sys.maxsize > 2 ** 32)
    return lib


_native_lib_handle = load_lib()


def decode_tile_native(tile_data_clip):
    tile = tile_data_clip[0]
    data = tile_data_clip[1]
    clip_tile = tile_data_clip[2]
    decoded_data = None
    if not tile.decoded_data:
        try:
            # with open(r"c:\temp\uster.pbf", 'wb') as f:
            #     f.write(tile_data_tuple[1])
            # encoded_data = bytearray(tile_data_tuple[1])
            encoded_data = bytearray(data)

            hex_string = "".join("%02x" % b for b in encoded_data)
            hex_bytes = hex_string.encode(encoding="UTF-8")

            tile_span_x = tile.extent[2] - tile.extent[0]
            tile_span_y = tile.extent[1] - tile.extent[3]
            tile_x = tile.extent[0]
            tile_y = tile.extent[1] - tile_span_y  # subtract tile size because Y starts from top, not from bottom

            ptr = _native_lib_handle.decodeMvtToJson(
                clip_tile,
                int(tile.zoom_level),
                int(tile.column),
                int(tile.row),
                tile_x,
                tile_y,
                tile_span_x,
                tile_span_y,
                hex_bytes,
            )
            decoded_data = cast(ptr, c_char_p).value
            _native_lib_handle.freeme(ptr)

            # with open(r"c:\temp\output.txt", 'w') as f:
            #     f.write(decoded_data)
            decoded_data = json.loads(decoded_data)
        except:
            info("Decoding failed: {}", sys.exc_info()[1])
            # with open(r"c:\temp\output.txt", 'w') as f:
            #     f.write(decoded_data)

    return tile, decoded_data
