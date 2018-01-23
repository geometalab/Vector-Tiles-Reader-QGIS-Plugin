[![Build Status](https://travis-ci.org/geometalab/Vector-Tiles-Reader-QGIS-Plugin.svg?branch=master)](https://travis-ci.org/geometalab/Vector-Tiles-Reader-QGIS-Plugin)
[![Coverage Status](https://coveralls.io/repos/github/geometalab/Vector-Tiles-Reader-QGIS-Plugin/badge.svg?branch=HEAD)](https://coveralls.io/github/geometalab/Vector-Tiles-Reader-QGIS-Plugin?branch=HEAD)

# Vector Tiles Reader QGIS-Plugin

This Python plugin reads Mapbox Vector Tiles (MVT) from vector tile servers, local MBTiles files or from a directory in zxy structure.

## Help
A help can be found here: https://github.com/geometalab/Vector-Tiles-Reader-QGIS-Plugin/wiki/Help

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

## Docker Tests

```
docker-compose build qgis2
docker-compose run -d --name qgis2 qgis2
docker exec -it qgis2 sh -c "qgis_testrunner.sh vector_tiles_reader"
```


## Technical documentation

Name conventions for Vector Tiles Reader QGIS Plugin:

* Official full name : "Vector Tiles Reader" or "Vector Tiles Reader QGIS Plugin"
* Camel Case no space: VectorTilesReader
* Lower Case no space: vector_tiles_reader
* Abbreviated name   : vtr

## Requirements
* QGIS 2.18
* This Plugin was tested on Ubuntu 16.10, Windows 10 and OSX

## Installation
### QGIS Plugins
Download the latest published release inside QGIS:
1. _Plugins_ -> _Manage and Install Plugins..._
2. Under 'Settings', enable 'Show experimental plugins'
3. Search for 'Vector Tiles Reader'
4. Install

### Windows
Copy cloned folder or create symlink to: 
%userprofile%/.qgis2/python/plugins

To create the symlink open a command prompt as Administrator and run:

```
mklink /D "%userprofile%/.qgis2/python/plugins/vector_tiles_reader" X:\{YourPathToTheCloned}\vector_tiles_reader
```

### Ubuntu
```
ln -sr ./ ~/.qgis2/python/plugins/Vector-Tile-Reader
```

## FAQ

#### How can I use the server connection feature?

Any vector tile service, implementing the [TileJSON specification](https://github.com/mapbox/tilejson-spec/tree/master/2.2.0)  should work.

For the feature to work, you have to create a connection using a URL pointing to the TileJSON of the tile service.

For example you can use **http://free&#46;tilehosting&#46;com/data/v3.json?key={API-KEY}** and get your own API-Key from [OpenMapTiles.com](https://openmaptiles.com/hosting/)
