import mapbox_vector_tile
from ctypes import *
import json
import sys
import os

from log_helper import info, warn


def decode_tile(tile_data_tuple):
    tile = tile_data_tuple[0]
    if not tile.decoded_data:
        encoded_data = tile_data_tuple[1]
        tile.decoded_data = mapbox_vector_tile.decode(encoded_data)
    return tile


def get_lib_for_current_platform():
    is_64_bit = sys.maxsize > 2**32
    if is_64_bit:
        bitness_string = "x86_64"
    else:
        bitness_string = "i686"
    lib = None
    if sys.platform.startswith("linux"):
        lib = "pbf2geojson_{}.so".format(bitness_string)
    elif sys.platform.startswith("win32"):
        lib = "pbf2geojson_{}.dll".format(bitness_string)
    elif sys.platform.startswith("darwin"):
        pass
    if lib:
        lib = os.path.join(os.path.abspath(os.path.dirname(__file__)), "ext-libs", "pbf2geojson", lib)
    return lib


def can_load_lib():
    return load_lib() is not None


def load_lib():
    lib = None
    path = get_lib_for_current_platform()
    if path:
        try:
            lib = cdll.LoadLibrary(path)
            lib.decodeMvtToJson.argtypes = [c_double, c_double, c_double, c_double, c_char_p]
            lib.decodeMvtToJson.restype = c_void_p
            lib.freeme.argtypes = [c_void_p]
            lib.freeme.restype = None
        except:
            warn("Loading lib failed for platform '{}': {}", sys.platform, path)
    else:
        warn("No prebuilt binary found for: {}, 64bit={}", sys.platform, sys.maxsize > 2**32)
    return lib


def decode_tile_native(tile_data_tuple):
    if sys.platform.startswith("win32"):
        extend_path()
    tile = tile_data_tuple[0]
    if not tile.decoded_data:
        try:
            # with open(r"c:\temp\uster.pbf", 'wb') as f:
            #     f.write(tile_data_tuple[1])
            encoded_data = bytearray(tile_data_tuple[1])

            hex_string = "".join("%02x" % b for b in encoded_data)

            tile_span_x = tile.extent[2] - tile.extent[0]
            tile_span_y = tile.extent[1] - tile.extent[3]
            tile_x = tile.extent[0]
            tile_y = tile.extent[1] - tile_span_y  # subtract tile size because Y starts from top, not from bottom

            lib = load_lib()
            ptr = lib.decodeMvtToJson(tile_x, tile_y, tile_span_x, tile_span_y, hex_string)
            decoded_data = cast(ptr, c_char_p).value
            lib.freeme(ptr)

            # with open(r"c:\temp\output.txt", 'w') as f:
            #     f.write(decoded_data)
            tile.decoded_data = json.loads(decoded_data)
        except:
            info("error: {}", sys.exc_info())
    return tile


def extend_path():
    os.environ["path"] = os.environ["path"] + ";" + "C:\\Users\\Martin\\Anaconda2\\Lib\\site-packages\\PyQt4;"\
                                                    "C:\\WINDOWS\\system32;C:\\WINDOWS;C:\\WINDOWS\\System32\\Wbem;"\
                                                    "C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\;"\
                                                    "C:\\Program Files (x86)\\Windows Kits\\10\\Windows Performance Toolkit\\;"\
                                                    "C:\\Python27\\Scripts\\;C:\\Python27\\;C:\\Users\\Martin\\Anaconda2;C:\\Users\\Martin\\Anaconda2\\Scripts;C:\\Users\\Martin\\Anaconda2\\Library\\bin;"\
                                                    "C:\\Users\\Martin\\AppData\\Local\\Microsoft\\WindowsApps;"\
                                                    "C:\\Temp\\cmake-3.8.0-rc1-win64-x64\\bin;"\
                                                    "C:\\Temp\\protoc_build\\protobuf\\cmake;"\
                                                    "C:\\Users\\Martin\\Anaconda2\\Lib\\site-packages\\PyQt4;"\
                                                    "C:\\Program Files\\QGIS 2.18\\bin;C:\\Program Files\\QGIS 2.18\\apps\\qgis\\bin;"\
                                                    "C:\\cygwin64\\bin;C:\\DEV\\vtzero\\examples;"
