#include "utils.hpp"

#include <vtzero/vector_tile.hpp>

#include <fstream>
#include <getopt.h>
#include <iostream>
#include <sstream>
#include <string>

struct my_geom_handler_points {

	int extent;
	float (&tile_coords)[4];
	std::stringstream& output;

    void points_begin(uint32_t /*count*/) const noexcept {
		output << '[';
    }

    void points_point(const vtzero::point point) const {
		float delta_x = tile_coords[2] - tile_coords[0];
		float delta_y = tile_coords[3] - tile_coords[1];
		float merc_easting = tile_coords[0] + delta_x / extent * point.x;
		float merc_northing = tile_coords[1] + delta_y / extent * point.y;
        output << merc_easting << ',' << merc_northing;
    }

    void points_end() const noexcept {
		output << ']';
    }

};

struct my_geom_handler_linestrings {

	int extent;
	float (&tile_coords)[4];
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
		float delta_x = tile_coords[2] - tile_coords[0];
		float delta_y = tile_coords[3] - tile_coords[1];
		float merc_easting = tile_coords[0] + delta_x / extent * point.x;
		float merc_northing = tile_coords[1] + delta_y / extent * point.y;

		temp += '[';
		temp +=  std::to_string(merc_easting);
        temp +=  ",";
        temp +=  std::to_string(merc_northing);
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
	float (&tile_coords)[4];
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
		float delta_x = tile_coords[2] - tile_coords[0];
		float delta_y = tile_coords[3] - tile_coords[1];
		float merc_easting = tile_coords[0] + delta_x / extent * point.x;
		float merc_northing = tile_coords[1] + delta_y / extent * point.y;

		temp += '[';
		temp +=  std::to_string(merc_easting);
        temp +=  ',';
        temp +=  std::to_string(merc_northing);
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

void getJson(float (&tile_extent)[4], const vtzero::layer& layer, std::stringstream& result) {
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
				vtzero::decode_point_geometry(feature.geometry(), true, my_geom_handler_points{extent, tile_extent, result});
				result << ", \"type\": \"Point\"";
				break;
			case vtzero::GeomType::LINESTRING:
				vtzero::decode_linestring_geometry(feature.geometry(), true, my_geom_handler_linestrings{extent, tile_extent, isMulti, coordinatesString});
				if (isMulti) {
					result << '[' << coordinatesString << ']';
					result << ", \"type\": \"MultiLineString\"";
				} else {
					result << coordinatesString;
					result << ", \"type\": \"LineString\"";
				}

				break;
			case vtzero::GeomType::POLYGON:
				vtzero::decode_polygon_geometry(feature.geometry(), true, my_geom_handler_polygons{extent, isMulti, tile_extent, coordinatesString});
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


const char* decodeAsJson(float (&tile_extent)[4], const char* hex){
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
	   getJson(tile_extent, layer, test);
	}

	test << "]}";

	static std::string result = test.str();
	return result.c_str();
}

extern "C" {
	const char* decodeMvtToJson(const float f1, const float f2, const float f3, const float f4, const char* data)
	{
		float arr[4] = {f1,f2,f3,f4};
		return decodeAsJson(arr, data);
	}
}