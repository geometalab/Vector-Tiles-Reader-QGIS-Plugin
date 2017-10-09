from ctypes import *
import json
import sys
import os

from log_helper import info


def decode_tile_cpp(tile_data_tuple):
    # self.extend_path()
    tile = tile_data_tuple[0]
    if not tile.decoded_data:
        try:
            # with open(r"c:\temp\uster.pbf", 'wb') as f:
            #     f.write(tile_data_tuple[1])
            encoded_data = bytearray(tile_data_tuple[1])

            hex_string = "".join("%02x" % b for b in encoded_data)

            tileSpanX = tile.extent[2] - tile.extent[0]
            tileSpanY = tile.extent[1] - tile.extent[3]
            tileX = tile.extent[0]
            tileY = tile.extent[1] - tileSpanY  # subtract tile size because Y starts from top, not from bottom

            lib = cdll.LoadLibrary(r"C:\DEV\vtzero\examples\pbf2geojson.dll")
            decode_mvt = lib.decodeMvtToJson
            decode_mvt.argtypes = [c_double, c_double, c_double, c_double, c_char_p]
            decode_mvt.restype = c_void_p
            lib.freeme.argtypes = [c_void_p]
            lib.freeme.restype = None

            ptr = decode_mvt(tileX, tileY, tileSpanX, tileSpanY, hex_string)
            decoded_data = cast(ptr, c_char_p).value
            lib.freeme(ptr)

            # with open(r"c:\temp\output.txt", 'w') as f:
            #     f.write(decoded_data)
            tile.decoded_data = json.loads(decoded_data)
        except:
            info("error: {}", sys.exc_info())
    return tile


def extend_path():
    os.environ["path"] = os.environ["path"] + ";" + "C:\\Users\\Martin\\Anaconda2\\Lib\\site-packages\\PyQt4;C:\\Program Files (x86)\\NVIDIA Corporation\\PhysX\\Common;C:\\GTK\\bin;C:\\ProgramData\\Oracle\\Java\\javapath;C:\\WINDOWS\\system32;C:\\WINDOWS;C:\\WINDOWS\\System32\\Wbem;C:\\WINDOWS\\System32\\WindowsPowerShell\\v1.0\\;C:\\Program Files (x86)\\Common Files\\Acronis\\VirtualFile\\;C:\\Program Files (x86)\\Common Files\\Acronis\\VirtualFile64\\;C:\\Program Files (x86)\\Common Files\\Acronis\\SnapAPI\\;C:\\Program Files\\Microsoft SQL Server\\120\\Tools\\Binn\\;C:\\Program Files\\Microsoft\\Web Platform Installer\\;C:\\Program Files (x86)\\GtkSharp\\2.12\\bin;C:\\Program Files\\Microsoft SQL Server\\130\\Tools\\Binn\\;C:\\Program Files (x86)\\Windows Kits\\10\\Windows Performance Toolkit\\;C:\\Program Files\\dotnet\\;C:\\Program Files\\Git\\cmd;C:\\Program Files\\Microsoft DNX\\Dnvm\\;C:\\Program Files (x86)\\Skype\\Phone\\;C:\\Program Files\\PuTTY\\;C:\\Program Files\\nodejs\\;C:\\Python27\\Scripts\\;C:\\Python27\\;C:\\Users\\Martin\\Anaconda2;C:\\Users\\Martin\\Anaconda2\\Scripts;C:\\Users\\Martin\\Anaconda2\\Library\\bin;C:\\Program Files (x86)\\Microsoft VS Code\\bin;C:\\Users\\Martin\\AppData\\Local\\Microsoft\\WindowsApps;C:\\Temp\\cmake-3.8.0-rc1-win64-x64\\bin;C:\\Temp\\protoc_build\\protobuf\\cmake;C:\\virtuoso-opensource\\bin;C:\\Users\\Martin\\Anaconda2\\Lib\\site-packages\\PyQt4;C:\\Program Files\\QGIS 2.18\\bin;C:\\Program Files\\QGIS 2.18\\apps\\qgis\\bin;C:\\Program Files\\PostgreSQL\\9.6\\bin;C:\\Users\\Martin\\AppData\\Roaming\\npm;C:\\cygwin64\\bin;C:\\DEV\\vtzero\\examples;"
