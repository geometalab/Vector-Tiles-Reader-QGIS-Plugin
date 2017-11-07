ifeq ($(OS),Windows_NT)
    detected_OS := Windows
else
    detected_OS := $(shell sh -c 'uname -s 2>/dev/null || echo not')
endif

CXXFLAGS = -std=c++11 -Iinclude -I../protozero/include -I../vtzero/include -s -Os -Ofast -O3 --shared
ifeq ($(detected_OS),Windows)
    CXXFLAGS += -static -static-libgcc -static-libstdc++ -Wl,-Bstatic
endif
ifeq ($(detected_OS),Linux)
    CXXFLAGS += -fPIC
endif
ifeq ($(detected_OS),Darwin)
    CXXFLAGS += -fPIC
    CXX = clang++
endif


windows32:
	x86_64-w64-mingw32-g++ $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_x86_64.dll ./ext-libs/pbf2geojson/pbf2geojson.cpp
	
windows64:
	i686-w64-mingw32-g++ $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_x86_64.dll ./ext-libs/pbf2geojson/pbf2geojson.cpp
	
windows: windows32 windows64

linux:
	$(CXX) -m64 $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_x86_64.so ./ext-libs/pbf2geojson/pbf2geojson.cpp
	$(CXX) -m32 $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_i686.so ./ext-libs/pbf2geojson/pbf2geojson.cpp

osx:
	$(CXX) -m64 $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_x86_64_osx.so ./ext-libs/pbf2geojson/pbf2geojson.cpp
	$(CXX) -m32 $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_i686_osx.so ./ext-libs/pbf2geojson/pbf2geojson.cpp
