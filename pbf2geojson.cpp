#include "utils.hpp"

#include <vtzero/vector_tile.hpp>

#include <fstream>
#include <getopt.h>
#include <iostream>
#include <sstream>
#include <string>

struct geom_handler_points {

    void points_begin(uint32_t /*count*/) const noexcept {
    }

    void points_point(const vtzero::point point) const {
        std::cout << "      POINT(" << point.x << ',' << point.y << ")\n";
    }

    void points_end() const noexcept {
    }

};

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

struct geom_handler_linestrings {

    std::string output{};
	int ringCounter = 0;

    void linestring_begin(uint32_t count) {
        output = "      LINESTRING[count=";
        output += std::to_string(count);
        output += "](";
    }

    void linestring_point(const vtzero::point point) {
        output += std::to_string(point.x);
        output += ' ';
        output += std::to_string(point.y);
        output += ',';
    }

    void linestring_end() {
		if (ringCounter > 0) {

		}

        if (output.empty()) {
            return;
        }
        if (output.back() == ',') {
            output.resize(output.size() - 1);
        }
        output += ")\n";
        std::cout << output;

		ringCounter++;
    }

};

struct geom_handler_polygons {

    std::string output{};

    void ring_begin(uint32_t count) {
        output = "      RING[count=";
        output += std::to_string(count);
        output += "](";
    }

    void ring_point(const vtzero::point point) {
        output += std::to_string(point.x);
        output += ' ';
        output += std::to_string(point.y);
        output += ',';
    }

    void ring_end(bool is_outer) {
        if (output.empty()) {
            return;
        }
        if (output.back() == ',') {
            output.back() = ')';
        }
        if (is_outer) {
            output += "[OUTER]\n";
        } else {
            output += "[INNER]\n";
        }
        std::cout << output;
    }

};

struct print_value {

    template <typename T>
    void operator()(const T& value) const {
        std::cout << value;
    }

    void operator()(const vtzero::data_view& value) const {
        std::cout << '"';
        std::cout.write(value.data(), value.size());
        std::cout << '"';
    }

}; // struct print_value

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

void print_layer(const vtzero::layer& layer, bool strict, bool print_tables, bool print_values_with_type) {
    std::cout << "layer:\n"
              << "  name:    " << std::string{layer.name()} << '\n'
              << "  version: " << layer.version() << '\n'
              << "  extent:  " << layer.extent() << '\n';

    if (print_tables) {
        std::cout << "  keys:\n";
        int n = 0;
        for (const auto& key : layer.key_table()) {
            std::cout << "    " << n++ << ": ";
            std::cout.write(key.data(), key.size());
            std::cout << '\n';
        }
        std::cout << "  values:\n";
        n = 0;
        for (const vtzero::value_view& value : layer.value_table()) {
            std::cout << "    " << n++ << ": ";
            vtzero::apply_visitor(print_value{}, value);
            if (print_values_with_type) {
                std::cout << " [" << vtzero::property_value_type_name(value.type()) << "]\n";
            } else {
                std::cout << '\n';
            }
        }
    }

    for (const auto feature : layer) {
        std::cout << "  feature:\n"
                  << "    id:       ";
        if (feature.has_id()) {
            std::cout << feature.id() << '\n';
        } else {
            std::cout << "(none)\n";
        }
        std::cout << "    geomtype: " << vtzero::geom_type_name(feature.type()) << '\n'
                  << "    geometry:\n";
        switch (feature.type()) {
            case vtzero::GeomType::POINT:
                vtzero::decode_point_geometry(feature.geometry(), strict, geom_handler_points{});
                break;
            case vtzero::GeomType::LINESTRING:
                vtzero::decode_linestring_geometry(feature.geometry(), strict, geom_handler_linestrings{});
                break;
            case vtzero::GeomType::POLYGON:
                vtzero::decode_polygon_geometry(feature.geometry(), strict, geom_handler_polygons{});
                break;
            default:
                std::cout << "UNKNOWN GEOMETRY TYPE\n";
        }
        std::cout << "    properties:\n";
        for (auto property : feature) {
            std::cout << "      ";
            std::cout.write(property.key().data(), property.key().size());
            std::cout << '=';
            vtzero::apply_visitor(print_value{}, property.value());
            if (print_values_with_type) {
                std::cout << " [" << vtzero::property_value_type_name(property.value().type()) << "]\n";
            } else {
                std::cout << '\n';
            }
        }
    }
}

void print_json(const vtzero::layer& layer) {
	std::string result;

	std::cout << std::string{layer.name()} << ": {" << std::endl;
	std::cout << "features: [" << std::endl;

    for (const auto feature : layer) {
        std::cout << " {" << std::endl;
        std::cout << "id: ";
        if (feature.has_id()) {
            std::cout << feature.id();
        }

        std::cout << ",\n";

        std::cout << "type: " << vtzero::geom_type_name(feature.type()) << ",\n"
                  << "geometry: ";

		switch (feature.type()) {
            case vtzero::GeomType::POINT:
                vtzero::decode_point_geometry(feature.geometry(), true, geom_handler_points{});
                break;
            case vtzero::GeomType::LINESTRING:
                vtzero::decode_linestring_geometry(feature.geometry(), true, geom_handler_linestrings{});
                break;
            case vtzero::GeomType::POLYGON:
                vtzero::decode_polygon_geometry(feature.geometry(), true, geom_handler_polygons{});
                break;
            default:
                std::cout << "UNKNOWN GEOMETRY TYPE\n";
        }

		std::cout << ",\n";

        std::cout << "properties: {\n";
        for (auto property : feature) {
            std::cout << "'";
            std::cout.write(property.key().data(), property.key().size());
            std::cout << "': ";
            vtzero::apply_visitor(print_value{}, property.value());
            std::cout << ",\n";
        }
		std::cout << "}\n}";
		break;
    }

	std::cout << "]\n}" << std::endl;
}

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

		std::stringstream bla;
        // result << "type: " << vtzero::geom_type_name(feature.type()) << ", geometry: ";
		//result << "type: " << static_cast<int>(feature.type()) << ", geometry: ";

		//result << "\"geometry\": { \"type\": \"" << vtzero::geom_type_name(feature.type()) << "\", \"coordinates\":";

		std::string coordinatesString = "";
		bool isMulti = false;
		result << "\"geometry\": { \"coordinates\":";
		switch (feature.type()) {
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
            //std::cout.write(property.key().data(), property.key().size());

            vtzero::apply_visitor(my_print_value{result}, property.value());
        }
		result << "}}";
		//break;
    }

	result << "]\n}";
}

void print_layer_overview(const vtzero::layer& layer) {
    std::cout.write(layer.name().data(), layer.name().size());
    std::cout << ' ' << layer.size() << '\n';
}

void print_help() {
    std::cout << "vtzero-show [OPTIONS] VECTOR-TILE [LAYER-NUM|LAYER-NAME]\n\n"
              << "Dump contents of vector tile.\n"
              << "\nOptions:\n"
              << "  -h, --help         This help message\n"
              << "  -l, --layers       Show layer overview\n"
              << "  -s, --strict       Use strict geometry parser\n"
              << "  -t, --tables       Also print key/value tables\n";
}

void print(const std::string& filename){


			std::cout << "Load mvt: " << filename << std::endl;

			const auto data = read_file(filename);
			vtzero::vector_tile tile{data};

			std::cout << "{\n";
			for (const auto layer : tile) {
               //print_layer_overview(layer);
			   print_json(layer);
			}
			std::cout << "}";

			//return "hello world output";
}


void decode(const char* data){
		std::string str(data);
		std::string res;
		res.reserve(str.size() / 2);
		for (int i = 0; i < int(str.size()); i += 2)
		{
			std::istringstream iss(str.substr(i, 2));
			int temp;
			iss >> std::hex >> temp;
			res += static_cast<char>(temp);
		}
		std::cout << res;

			//const std::string data(my_data);
			std::cout << "Begin decode: " << std::endl;
			vtzero::vector_tile tile{res};

			for (const auto layer : tile) {
               print_layer_overview(layer);
			}

            std::cout << "End decode" << std::endl;
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
	test.flush();

	static std::string result = test.str();
	return result.c_str();
}

extern "C" {
	void print_tile(const char* filename) { print(filename); }
	void decode_mvt(const char* data) { decode(data); }
	const char* decodeMvtToJson(const float f1, const float f2, const float f3, const float f4, const char* data)
	{
		float arr[4] = {f1,f2,f3,f4};
		return decodeAsJson(arr, data);
	}
}