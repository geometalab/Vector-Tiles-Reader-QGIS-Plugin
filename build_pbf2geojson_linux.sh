g++ -m64 -std=c++11 -Iinclude -I../protozero/include -I../vtzero/include -s -Os -Ofast -O3 --shared -fPIC -o ./ext-libs/pbf2geojson/pbf2geojson_x86_64.so ./ext-libs/pbf2geojson/pbf2geojson.cpp
