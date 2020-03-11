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
ifeq ($(detected_OS),OpenBSD)
    CXX = c++
endif
ifeq ($(detected_OS),Darwin)
    CXXFLAGS += -fPIC
    CXX = clang++
endif


windows32:
	i686-w64-mingw32-g++ $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_windows_i686.dll ./ext-libs/pbf2geojson/pbf2geojson.cpp

windows64:
	x86_64-w64-mingw32-g++ $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_windows_x86_64.dll ./ext-libs/pbf2geojson/pbf2geojson.cpp

windows64_dockcross:
	$(CXX) $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_windows_x86_64.dll ./ext-libs/pbf2geojson/pbf2geojson.cpp

windows32_dockcross:
	$(CXX) $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_windows_i686.dll ./ext-libs/pbf2geojson/pbf2geojson.cpp

windows: windows32 windows64

linux:
	$(CXX) -m64 $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_linux_x86_64.so ./ext-libs/pbf2geojson/pbf2geojson.cpp
	$(CXX) -m32 $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_linux_i686.so ./ext-libs/pbf2geojson/pbf2geojson.cpp

osx:
	$(CXX) -m64 $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_osx_x86_64.so ./ext-libs/pbf2geojson/pbf2geojson.cpp
	$(CXX) -m32 $(CXXFLAGS) -o ./ext-libs/pbf2geojson/pbf2geojson_osx_i686.so ./ext-libs/pbf2geojson/pbf2geojson.cpp

openbsd:
	$(CXX) -fPIC -std=c++11 -I/usr/local/include -s -Os -Ofast -O3 --shared -o ./ext-libs/pbf2geojson/pbf2geojson_openbsd_x86_64.so ./ext-libs/pbf2geojson/pbf2geojson.cpp
