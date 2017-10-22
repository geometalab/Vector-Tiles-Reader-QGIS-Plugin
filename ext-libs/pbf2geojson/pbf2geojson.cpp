#include <vtzero/vector_tile.hpp>
#include <vtzero/feature.hpp>

#include <fstream>
#include <getopt.h>
#include <iostream>
#include <sstream>
#include <string>
#include <iomanip>

struct tile_location {
	const double x;
	const double y;
	const double spanX;
	const double spanY;
};

struct Point {
    double x;
    double y;
};

struct BoundingBox {
    Point min;
    Point max;

    bool intersects(const BoundingBox &other) const {
      return
        (min.x < other.max.x) && (max.x > other.min.x) &&
        (min.y < other.max.y) && (max.y > other.min.y);
    }

    bool contains(const BoundingBox& other) const {
        return
            min.x <= other.min.x &&
            max.x >= other.max.x &&
            min.y <= other.min.y &&
            max.y >= other.max.y;
    }
};

struct my_geom_handler_points {

	int extent;
	tile_location& loc;
	std::stringstream& output;

    void points_begin(uint32_t /*count*/) const noexcept {
		output << '[';
    }

    void points_point(const vtzero::point point) const {
		auto absoluteX = loc.x + loc.spanX / extent * point.x;
		auto absoluteY = loc.y + loc.spanY / extent * point.y;
        output << absoluteX << ',' << absoluteY;
    }

    void points_end() const noexcept {
		output << ']';
    }
};

struct my_geom_handler_linestrings {

	int extent;
	tile_location& loc;
	std::string& result;

    bool alreadyBeenHere;
	std::string temp;

	int ringCounter;

    void linestring_begin(uint32_t count) {
		if (alreadyBeenHere) {
			temp = ",[";
		} else {
			temp = "[";
		}
		alreadyBeenHere = true;
    }

    void linestring_point(const vtzero::point point) {
		auto absoluteX = loc.x + loc.spanX / extent * point.x;
		auto absoluteY = loc.y + loc.spanY / extent * point.y;

		temp += '[';
		temp +=  std::to_string(absoluteX);
        temp +=  ",";
        temp +=  std::to_string(absoluteY);
        temp +=  "],";
    }

    void linestring_end() {
        // if (temp.back() == ',') {
            // temp.resize(temp.size() - 1);
        // }
        if (temp.back() == ',') {
            temp.back() = ' ';
        }
		temp += ']';
		result += temp;
    }
};

struct my_geom_handler_polygons {

    int extent;
	tile_location& loc;
	std::string& result;

    std::vector<std::vector<Point>>& rings;

	bool alreadyBeenHere;
	std::string temp;

    std::vector<Point> _currentRing;

    void ring_begin(uint32_t count) {
        _currentRing = std::vector<Point>();
//		if (alreadyBeenHere) {
//			temp = ",[";
//		} else {
//			temp = "[";
//		}
//		alreadyBeenHere = true;
    }

    void ring_point(const vtzero::point point) {
		auto absoluteX = loc.x + loc.spanX / extent * point.x;
		auto absoluteY = loc.y + loc.spanY / extent * point.y;

        _currentRing.push_back(Point{absoluteX, absoluteY});

//		temp += '[';
//		temp +=  std::to_string(absoluteX);
//        temp +=  ',';
//        temp +=  std::to_string(absoluteY);
//        temp +=  "],";
    }

    void ring_end(bool is_outer) {
        rings.push_back(_currentRing);
//        if (temp.back() == ',') {
//            temp.back() = ' ';
//        }
//		temp += ']';
//		result += temp;
    }
};

struct my_print_value {

	std::string& output;

    template <typename T>
    void operator()(const T& value) const {
        output += value;
    }

    void operator()(const vtzero::data_view& value) const {
        std::string val(value);
        std::ostringstream o;
        for (auto c = val.cbegin(); c != val.cend(); c++) {
            switch (*c) {
                case '"': o << "\\\""; break;
                case '\\': o << "\\\\"; break;
                case '\b': o << "\\b"; break;
                case '\f': o << "\\f"; break;
                case '\n': o << "\\n"; break;
                case '\r': o << "\\r"; break;
                case '\t': o << "\\t"; break;
                default:
                    if ('\x00' <= *c && *c <= '\x1f') {
                        o << "\\u"
                          << std::hex << std::setw(4) << std::setfill('0') << (int)*c;
                    } else {
                        o << *c;
                    }
            }
        }

        output += '"';
        output += o.str();
        output += '"';
    }
};

BoundingBox getBoundingBox(std::vector<Point>& ring) {
    int count = 0;
    Point min;
    Point max;
    for (auto p : ring) {
        if (count++ == 0) {
            min.x = p.x;
            min.y = p.y;
            max.x = p.x;
            max.y = p.y;
        } else {
            min.x = std::min(min.x, p.x);
            min.y = std::min(min.y, p.y);
            max.x = std::max(max.x, p.x);
            max.y = std::max(max.y, p.y);
        }
    }
    return BoundingBox{min, max};
}

std::string ringToString(std::vector<Point>& ring) {
    std::string result("[");
    int count = 0;
    for(auto p : ring) {
        if (count++>0) {
            result += ",[";
        } else {
            result += '[';
        }
        result += std::to_string(p.x);
        result += ',';
        result += std::to_string(p.y);
        result += ']';
    }
    result += ']';
    return result;
}

std::string ringsToString(std::vector<std::vector<Point>>& rings) {
    std::string result("[");
    int count = 0;
    for (auto r: rings) {
        if (count++>0) {
            result += ',';
        }
        result += ringToString(r);
    }
    result += ']';
    return result;
}

std::string getPolygonFeatures(std::string& id, std::string& properties, std::vector<std::vector<Point>>& rings, const bool& splitPolygons) {
    if (rings.size() == 0)
        return "";

    std::string result;

    std::vector<Point> mainRing = rings[0];

    std::vector<std::vector<Point>> mainRings;
    mainRings.push_back(mainRing);
    auto mainBox = getBoundingBox(mainRing);
    std::vector<std::vector<Point>> separateRings;

    auto nrRings = int(rings.size());
    if (!splitPolygons && nrRings > 1) {
        for (int i=1;i<nrRings; i++) {
            auto ring = rings[i];
            mainRings.push_back(ring);
        }
    } else if (splitPolygons && nrRings > 1) {
        for (int i=1;i<nrRings; i++) {
            auto ring = rings[i];
            auto newBox = getBoundingBox(ring);
            if (mainBox.contains(newBox)) {
                mainRings.push_back(ring);
            } else {
                separateRings.push_back(ring);
            }
        }
    }

    std::vector<std::string> coords;
    auto mainFeatureCoords = ringsToString(mainRings);
    coords.push_back(mainFeatureCoords);
    if (int(separateRings.size()) > 0) {
        for (auto r: separateRings) {
            std::string newRingString("[");
             newRingString += ringToString(r);
             newRingString += ']';
            coords.push_back(newRingString);
        }
    }

    int count = 0;
    for (auto c: coords) {
        if (count++>0) {
            result += ',';
        }
        result += "{\"id\":";
        result += id;
        result += ",\"type\":\"Feature\",\"geometry\":{\"coordinates\":[";

        result += c;
        result += "],\n\"type\":\"MultiPolygon\"";
        result += "},\"properties\":";
        result += properties;
        result += '}';
    }

    return result;
}


void getJson(tile_location& loc, vtzero::layer& layer, std::stringstream& result) {
	result << "\"" << std::string{layer.name()} << "\":{";
	int extent = layer.extent();
	result << "\"extent\":" << extent << ",";
	result << "\"isGeojson\":true,";
	result << "\"features\":[";

	int featureCount = 0;
	while (auto feature = layer.next_feature()) {
		if (featureCount++ > 0) {
			result << ',';
		}

        std::string id;
		if (feature.has_id()) {
		    id = std::to_string(feature.id());
		} else {
		    id = '0';
		}

		int propertyCount = 0;
		std::string properties = "{";
//		while (auto property = feature.next_property()) {
//			if (propertyCount++ > 0) {
//				properties += ',';
//			}
//			properties += "\"";
//			properties += std::string(property.key());
//			properties += "\":";
//			vtzero::apply_visitor(my_print_value{properties}, property.value());
//		}
		properties += '}';

        std::string coordinatesString("");
		if (feature.geometry_type() == vtzero::GeomType::POLYGON) {
            // todo: create multipolygon here by using method getPolygonFeatures
            std::vector<std::vector<Point>> rings;
            vtzero::decode_polygon_geometry(feature.geometry(), false, my_geom_handler_polygons{extent, loc, coordinatesString, rings});
            auto newFeatures = getPolygonFeatures(id, properties, rings, true);
            for(auto f : newFeatures) {
                result << f;
            }
		} else {
		    // todo: create handle point and linestring feature here
		    result << "{\"id\":" << id << ",\"type\":\"Feature\",\"properties\":" << properties << ",\"geometry\":{\"coordinates\":";
		    switch (feature.geometry_type()) {
                case vtzero::GeomType::POINT:
                    vtzero::decode_point_geometry(feature.geometry(), false, my_geom_handler_points{extent, loc, result});
                    result << ",\n\"type\": \"Point\"";
                    break;
                case vtzero::GeomType::LINESTRING:
                    vtzero::decode_linestring_geometry(feature.geometry(), false, my_geom_handler_linestrings{extent, loc, coordinatesString});
                        result << '[' << coordinatesString << ']';
                        result << ",\n\"type\":\"MultiLineString\"";
                    break;
                default:
                    result << "\"UNKNOWN GEOMETRY TYPE\"";
		    }
		    result << "}}";
		}


//		break;
	}
	result << "]}";
}


std::string decodeAsJson(tile_location& loc, const char* hex){
	std::string hexString(hex);
	std::string data;
	data.reserve(hexString.size() / 2);
	for (int i = 0; i < int(hexString.size()); i += 2)
	{
		std::istringstream iss(hexString.substr(i, 2));
		int temp;
		iss >> std::hex >> temp;
		data += static_cast<char>(temp);
	}

	std::stringstream test;

	vtzero::vector_tile tile{data};

	test << '{';
	int layerCount = 0;
	while (auto layer = tile.next_layer()) {
		if (layerCount++ > 0) {
			test << ',';
		}
	   getJson(loc, layer, test);
	}

	test << '}';

	return test.str();
}

extern "C" {
	char* decodeMvtToJson(const double tileX, const double tileY, const double tileSpanX, const double tileSpanY, const char* data) {
		tile_location loc{tileX, tileY, tileSpanX, tileSpanY};
		auto res = decodeAsJson(loc, data);
		const char* result = res.c_str();
		char *new_buf = strdup(result);
		return new_buf;
	}

	void freeme(char *ptr) {
		printf("freeing address: %p\n", ptr);
		free(ptr);
	}
}