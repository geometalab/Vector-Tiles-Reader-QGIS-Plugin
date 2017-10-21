#include <vtzero/vector_tile.hpp>

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

	bool alreadyBeenHere;
	std::string temp;

    void ring_begin(uint32_t count) {
		if (alreadyBeenHere) {
			temp = ",[";
		} else {
			temp = "[";
		}
		alreadyBeenHere = true;
    }

    void ring_point(const vtzero::point point) {
		auto absoluteX = loc.x + loc.spanX / extent * point.x;
		auto absoluteY = loc.y + loc.spanY / extent * point.y;

		temp += '[';
		temp +=  std::to_string(absoluteX);
        temp +=  ',';
        temp +=  std::to_string(absoluteY);
        temp +=  "],";
    }

    void ring_end(bool is_outer) {
        if (temp.back() == ',') {
            temp.back() = ' ';
        }
		temp += ']';
		result += temp;
    }
};

struct my_print_value {

	std::stringstream& output;

    template <typename T>
    void operator()(const T& value) const {
        output << value;
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

        output << '"' << o.str() << '"';
    }
};

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
		result << "{\"id\":";
		if (feature.has_id()) {
			result << feature.id() << ", ";
		} else {
			result << "0, ";
		}
		result << "\"type\":" << "\"Feature\",";

		std::string coordinatesString("");
		result << "\"geometry\":{\"coordinates\":";
		switch (feature.geometry_type()) {
			case vtzero::GeomType::POINT:
				vtzero::decode_point_geometry(feature.geometry(), false, my_geom_handler_points{extent, loc, result});
				result << ", \"type\": \"Point\"";
				break;
			case vtzero::GeomType::LINESTRING:
				vtzero::decode_linestring_geometry(feature.geometry(), false, my_geom_handler_linestrings{extent, loc, coordinatesString});
					result << '[' << coordinatesString << ']';
					result << ",\"type\":\"MultiLineString\"";
				break;
			case vtzero::GeomType::POLYGON:
				vtzero::decode_polygon_geometry(feature.geometry(), false, my_geom_handler_polygons{extent, loc, coordinatesString});
					result << "[[" << coordinatesString << "]]";
					result << ",\"type\":\"MultiPolygon\"";
				break;
			default:
				result << "UNKNOWN GEOMETRY TYPE\n";
		}
		result << "},\"properties\": {";

		int propertyCount = 0;
		std::string propertyValue;
		while (auto property = feature.next_property()) {
			if (propertyCount++ > 0) {
				result << ',';
			}
			result << "\"" << std::string(property.key()) << "\": ";
			vtzero::apply_visitor(my_print_value{result}, property.value());
		}
		result << "}}";
		//break;
	}
	result << "]\n}";
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