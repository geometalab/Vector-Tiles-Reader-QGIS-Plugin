# Vector Tiles Reader QGIS-Plugin

This Python plugin reads Mapbox Vector Tiles (MVT) from a local MBTiles file and loads them into a vector layer that is rendered by QGIS and it's (default) styling.

_>> This is work in progress! Expected release is around June 2017. <<_

For more information about the Vector Tiles concept and limitations of the plugin see homepage.

Important web links:
* __Homepage__ : http://giswiki.hsr.ch/Vector_Tiles_Reader_QGIS_Plugin
* Issues tracker : https://github.com/geometalab/Vector-Tiles-Reader-QGIS-Plugin/issues
* Code repository: https://github.com/geometalab/Vector-Tiles-Reader-QGIS-Plugin (this webpage)

## User Guide
A user guide can be found here: https://github.com/geometalab/Vector-Tiles-Reader-QGIS-Plugin/wiki/User-Guide#user-guide

## License

The Vector Tile Reader plugin is released under the GNU license (see LICENSE)

## Contributors

Vector Tile Reader has been developed by

* Martin Boos

Acknowledgments:

* Stefan Keller
* Dijan Helbling
* Nicola Jordan
* Raphael Das Gupta
* Carmelo Schumacher

## Technical documentation

Name conventions for Vector Tiles Reader QGIS Plugin:

* Official full name : "Vector Tiles Reader" or "Vector Tiles Reader QGIS Plugin"
* Camel Case no space: VectorTilesReader
* Lower Case no space: vector_tiles_reader
* Abbreviated name   : vtr

## Requirements
* QGIS 2.18
* This Plugin was tested on Ubuntu 16.10 and Windows 10

## Installation
### Windows
Copy cloned folder or create symlink to: 
%userprofile%/.qgis2/python/plugins

To create the symlink open a command prompt as Administrator and run:

**mklink /D "%userprofile%/.qgis2/python/plugins/vector_tiles_reader" X:\{YourPathToTheCloned}\vector_tiles_reader**

### Ubuntu
The script install.sh creates a symlink from the current directory to the qgis plugins directory

##FAQ
####How can I use the server connection feature?
Any vector tile service, implementing the [TileJSON specification](https://github.com/mapbox/tilejson-spec/tree/master/2.2.0)  should work.
For the feature to work, you have to create a connection using a URL pointing to the TileJSON of the tile service.

For example you can use **http://free&#46;tilehosting&#46;com/data/v3.json?key={API-KEY}** and get your own API-Key from [OpenMapTiles.com](https://openmaptiles.com/hosting/)
