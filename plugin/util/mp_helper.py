import os
import platform
import shutil
import sys
import traceback
from pathlib import Path
from datetime import datetime
from ctypes import c_bool, c_char_p, c_double, c_uint16, c_void_p, cast, cdll

import mapbox_vector_tile

from .file_helper import get_plugin_directory, get_temp_dir
from .log_helper import critical, info, warn

try:
    import simplejson as json
except ImportError:
    import json

_native_lib_handle = None


def decode_tile_python(tile_data_clip):
    tile = tile_data_clip[0]
    encoded_data = tile_data_clip[1]
    # clip_tile = tile_data_clip[2]

    decoded_data = None
    if encoded_data and not tile.decoded_data:
        decoded_data = mapbox_vector_tile.decode(encoded_data)
    return tile, decoded_data


def _get_lib_path():
    is_64_bit = sys.maxsize > 2 ** 32
    if is_64_bit:
        bitness_string = "x86_64"
    else:
        bitness_string = "i686"
    lib = None
    temp_lib_path = None
    if sys.platform.startswith("linux"):
        lib = "pbf2geojson_linux_{}.so".format(bitness_string)
    elif sys.platform.startswith("win32"):
        lib = "pbf2geojson_windows_{}.dll".format(bitness_string)
    elif sys.platform.startswith("darwin"):
        lib = "pbf2geojson_osx_{}.so".format(bitness_string)
    if lib:
        temp_dir = get_temp_dir("native")
        lib_path = os.path.join(os.path.abspath(get_plugin_directory()), "ext-libs", "pbf2geojson", lib)

        temp_lib_path = os.path.join(temp_dir, lib)
        if not os.path.isdir(temp_dir):
            os.makedirs(temp_dir)
        if os.path.isfile(temp_lib_path) and os.path.getmtime(temp_lib_path) != os.path.getmtime(lib_path):
            os.remove(temp_lib_path)
        if not os.path.isfile(temp_lib_path):
            shutil.copy2(lib_path, temp_dir)

    return temp_lib_path


def load_lib():
    global _native_lib_handle
    if _native_lib_handle:
        info("The native dll is already loaded, not loading again...")
    else:
        info("Loading native dll...")
        path = _get_lib_path()
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
                _native_lib_handle = lib
            except:
                warn("Loading lib failed for platform '{}': {}, {}", sys.platform, path, sys.exc_info()[1])
                _native_lib_handle = None
        else:
            warn("No prebuilt binary found for: {}, 64bit={}", sys.platform, sys.maxsize > 2 ** 32)
            _native_lib_handle = None


def unload_lib():
    global _native_lib_handle
    system = platform.system()
    try:
        info("Unloading native dll...")
        if _native_lib_handle:
            if system == "Windows":
                from ctypes import windll

                windll.kernel32.FreeLibrary(_native_lib_handle._handle)
            else:
                _native_lib_handle.dlclose()
        else:
            info("Dll already unloaded")
    except Exception:
        critical("Unloading native dll failed on {}: {}", system, sys.exc_info())
    finally:
        _native_lib_handle = None


def native_decoding_supported() -> bool:
    return _native_lib_handle is not None


def decode_tile_native(tile_data_clip):
    tile, data, clip_tile = tile_data_clip
    decoded_data = None
    if not tile.decoded_data:
        try:
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
            exc_txt = traceback.format_exc()
            info("Decoding failed: {}", exc_txt)
            from mapbox_vector_tile import decode
            tb_data = Path(get_temp_dir()) / f"decoding_data_{datetime.now()}.json".replace(" ", "_").replace(":", ".")
            tb_data.write_text(json.dumps(decode(data)))

    return tile, decoded_data
