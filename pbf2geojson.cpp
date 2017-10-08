#include "utils.hpp"

#include <vtzero/vector_tile.hpp>

#include <fstream>
#include <getopt.h>
#include <iostream>
#include <sstream>
#include <string>

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
	bool& isMulti;
	std::string& result;

	std::string temp;

	int ringCounter;

    void linestring_begin(uint32_t count) {
		if (++ringCounter > 1) {
			isMulti = true;
			temp = ",[";
		} else {
			temp = "[";
		}
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
        if (temp.empty()) {
            return;
        }
        if (temp.back() == ',') {
            temp.resize(temp.size() - 1);
        }
		temp += ']';
		result += temp;
    }
};

struct my_geom_handler_polygons {

    int extent;
	bool& isMulti;
	tile_location& loc;
	std::string& result;

	int ringCounter;
	std::string temp;

    void ring_begin(uint32_t count) {
		if (++ringCounter > 1) {
			temp = ",[[";
		} else {
			temp = "[[";
		}
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
        if (temp.empty()) {
            return;
        }

        if (temp.back() == ',') {
            temp.back() = ' ';
        }

		isMulti = !is_outer;
		temp += "]]";

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
        output << '"' << std::string(value) << '"';
    }
};

void getJson(tile_location& loc, const vtzero::layer& layer, std::stringstream& result) {
	result << "{ \"name\": \"" << std::string{layer.name()} << "\",";
	int extent = layer.extent();
	result << "\"extent\": " << extent << ", ";
	result << "\"geojsonFeatures\": [";

	int featureCount = 0;
	for (const auto feature : layer) {
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
		bool isMulti = false;
		result << "\"geometry\": { \"coordinates\":";
		switch (feature.geometry_type()) {
			case vtzero::GeomType::POINT:
				vtzero::decode_point_geometry(feature.geometry(), false, my_geom_handler_points{extent, loc, result});
				result << ", \"type\": \"Point\"";
				break;
			case vtzero::GeomType::LINESTRING:
				vtzero::decode_linestring_geometry(feature.geometry(), false, my_geom_handler_linestrings{extent, loc, isMulti, coordinatesString});
				if (isMulti) {
					result << '[' << coordinatesString << ']';
					result << ", \"type\": \"MultiLineString\"";
				} else {
					result << coordinatesString;
					result << ", \"type\": \"LineString\"";
				}

				break;
			case vtzero::GeomType::POLYGON:
				vtzero::decode_polygon_geometry(feature.geometry(), false, my_geom_handler_polygons{extent, isMulti, loc, coordinatesString});
				if (isMulti) {
					result << '[' << coordinatesString << ']';
					result << ", \"type\": \"MultiPolygon\"";
				} else {
					result << coordinatesString;
					result << ", \"type\": \"Polygon\"";
				}
				break;
			default:
				result << "UNKNOWN GEOMETRY TYPE\n";
		}
		result << "},\"properties\": {";

		int propertyCount = 0;
		for (auto property : feature) {
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


const char* decodeAsJson(tile_location& loc, const char* hex){
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

	test << "{ \"layers\": [";
	int layerCount = 0;
	for (const auto layer : tile) {
		if (layerCount++ > 0) {
			test << ',';
		}
	   getJson(loc, layer, test);
	}

	test << "]}";

	static std::string result = test.str();
	return result.c_str();
}

extern "C" {
	const char* decodeMvtToJson(const double tileX, const double tileY, const double tileSpanX, const double tileSpanY, const char* data)
	{
		tile_location loc{tileX, tileY, tileSpanX, tileSpanY};
		return decodeAsJson(loc, data);
	}
}