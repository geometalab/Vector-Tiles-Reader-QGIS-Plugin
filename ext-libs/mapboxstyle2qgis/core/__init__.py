import os
import json
import copy
import colorsys
from itertools import groupby
from xml.sax.saxutils import escape
from .xml_helper import create_style_file


def register_qgis_expressions():
    try:
        from qgis.core import QgsExpression
        from .data import qgis_functions
        QgsExpression.registerFunction(qgis_functions.get_zoom_for_scale)
        QgsExpression.registerFunction(qgis_functions.if_not_exists)
        QgsExpression.registerFunction(qgis_functions.interpolate_exp)
    except ImportError:
        print("registering functions failed")
        pass


def generate_styles(text, output_directory):
    """
     * Creates and exports the styles
    :param text:
    :param output_directory:
    :return:
    """

    styles = process(text)
    write_styles(styles_by_target_layer=styles, output_directory=output_directory)


def process(text):
    """
     * Creates the style definitions and returns them mapped by filename
    :param text:
    :return:
    """

    js = json.loads(text)
    layers = js["layers"]
    styles_by_file_name = {}
    for l in layers:
        if "source-layer" in l:
            layer_type = l["type"]
            source_layer = l["source-layer"]
            if layer_type == "fill":
                geo_type_name = ".polygon"
            elif layer_type == "line":
                geo_type_name = ".linestring"
            elif layer_type == "symbol":
                geo_type_name = ""
            else:
                continue

            file_name = "{}{}.qml".format(source_layer, geo_type_name)
            if file_name not in styles_by_file_name:
                styles_by_file_name[file_name] = {
                    "file_name": file_name,
                    "type": layer_type,
                    "styles": []
                }
            qgis_styles = get_styles(l)
            filter_expr = None
            if "filter" in l:
                filter_expr = get_qgis_rule(l["filter"])
            for s in qgis_styles:
                s["rule"] = filter_expr
            styles_by_file_name[file_name]["styles"].extend(qgis_styles)

    for layer_name in styles_by_file_name:
        styles = styles_by_file_name[layer_name]["styles"]
        for index, style in enumerate(styles):
            rule = style["rule"]
            name = style["name"]
            zoom = style["zoom_level"]
            styles_with_same_target = filter(lambda s: s["name"] != name and s["rule"] == rule and s["zoom_level"] <= zoom, styles[:index])
            groups_by_name = list(groupby(styles_with_same_target, key=lambda s: s["name"]))
            style["rendering_pass"] = len(groups_by_name)

    _add_default_transparency_styles(styles_by_file_name)
    return styles_by_file_name


def _add_default_transparency_styles(style_dict):
    for t in ["point", "linestring", "polygon"]:
        file_name = "transparent.{}.qml".format(t)
        style_dict[file_name] = {
            "styles": [],
            "file_name": file_name,
            "layer-transparency": 100,
            "type": None
        }


def write_styles(styles_by_target_layer, output_directory):
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)
    for layer_name in styles_by_target_layer:
        style = styles_by_target_layer[layer_name]
        create_style_file(output_directory=output_directory, layer_style=style)


_comparision_operators = {
    "==": "=",
    "<=": "<=",
    ">=": ">=",
    "<": "<",
    ">": ">",
    "!=": "!="
}

_combining_operators = {
    "all": "and",
    "any": "or",
    "none": "and not"
}

_membership_operators = {
    "in": "in",
    "!in": "not in"
}

_existential_operators = {
    "has": "is not null",
    "!has": "is null"
}

"""
 * the upper bound map scales by zoom level.
 * E.g. a style for zoom level 14 shall be applied for map scales <= 50'000
 * If the are more zoom levels applied, they need to be ascending.
 * E.g. a second style will be applied for zoom level 15, that is map scale <= 25'000, the first style
   for zoom level 14 will no longer be active.
"""
upper_bound_map_scales_by_zoom_level = {
    0: 1000000000,
    1: 1000000000,
    2: 500000000,
    3: 200000000,
    4: 50000000,
    5: 25000000,
    6: 12500000,
    7: 6500000,
    8: 3000000,
    9: 1500000,
    10: 750000,
    11: 400000,
    12: 200000,
    13: 100000,
    14: 50000,
    15: 25000,
    16: 12500,
    17: 5000,
    18: 2500,
    19: 1500,
    20: 750,
    21: 500,
    22: 250,
    23: 100,
    24: 0
}


def get_styles(layer):
    layer_id = layer["id"]
    if "type" not in layer:
        raise RuntimeError("'type' not set on layer")

    layer_type = layer["type"]

    base_style = {
        "zoom_level": None,
        "min_scale_denom": None,
        "max_scale_denom": None
    }

    if layer_id:
        base_style["name"] = layer_id

    resulting_styles = []
    values_by_zoom = {}

    all_values = []
    if layer_type == "fill":
        all_values.extend(get_properties_by_zoom(layer, "paint/fill-color", is_color=True, default="rgba(0,0,0,0)"))
        all_values.extend(get_properties_by_zoom(layer, "paint/fill-outline-color", is_color=True))
        all_values.extend(get_properties_by_zoom(layer, "paint/fill-translate"))
        all_values.extend(get_properties_by_zoom(layer, "paint/fill-opacity"))
    elif layer_type == "line":
        all_values.extend(get_properties_by_zoom(layer, "layout/line-join"))
        all_values.extend(get_properties_by_zoom(layer, "layout/line-cap"))
        all_values.extend(get_properties_by_zoom(layer, "paint/line-width", default=0, can_interpolate=True))
        all_values.extend(get_properties_by_zoom(layer, "paint/line-color", is_color=True, default="rgba(0,0,0,0)"))
        all_values.extend(get_properties_by_zoom(layer, "paint/line-opacity"))
        all_values.extend(get_properties_by_zoom(layer, "paint/line-dasharray"))
    elif layer_type == "symbol":
        all_values.extend(get_properties_by_zoom(layer, "layout/text-font"))
        all_values.extend(get_properties_by_zoom(layer, "layout/text-size", can_interpolate=True))
        all_values.extend(get_properties_by_zoom(layer, "layout/text-field", is_expression=True))
        all_values.extend(get_properties_by_zoom(layer, "layout/text-max-width"))
        all_values.extend(get_properties_by_zoom(layer, "paint/text-color", is_color=True))
        all_values.extend(get_properties_by_zoom(layer, "paint/text-halo-width", can_interpolate=True))
        all_values.extend(get_properties_by_zoom(layer, "paint/text-halo-color", is_color=True))

    for v in all_values:
        zoom = v["zoom_level"]
        if zoom is None:
            base_style[v["name"]] = v["value"]
        else:
            if zoom not in values_by_zoom:
                values_by_zoom[zoom] = []
            values_by_zoom[zoom].append(v)

    if "minzoom" in layer:
        minzoom = int(layer["minzoom"])
        values_by_zoom[minzoom] = []
    if "maxzoom" in layer:
        maxzoom = int(layer["maxzoom"])
        values_by_zoom[maxzoom] = []

    if not values_by_zoom:
        resulting_styles.append(base_style)
    else:
        clone = base_style
        for zoom in sorted(values_by_zoom.keys()):
            values = values_by_zoom[zoom]
            clone = copy.deepcopy(clone)
            clone["zoom_level"] = zoom
            for v in values:
                clone[v["name"]] = v["value"]
            resulting_styles.append(clone)
        styles_backwards = list(reversed(resulting_styles))
        for index, s in enumerate(styles_backwards):
            if index < len(resulting_styles)-1:
                next_style = styles_backwards[index+1]
                for k in s:
                    if k not in next_style:
                        next_style[k] = s[k]

    resulting_styles = sorted(resulting_styles, key=lambda s: s["zoom_level"])
    _apply_scale_range(resulting_styles)

    return resulting_styles


def _parse_expr(expr):
    if not expr:
        return expr
    fields = expr.replace("{", '"').replace("}", '"').replace("\n", " ").strip().split(" ")
    if fields:
        return escape_xml(fields[0])
        expr = _get_field_expr(0, fields)
    # fields = map(lambda (index, f): _get_field_expr(index, f), enumerate(fields))
    expr = "+".join(fields)
    return escape_xml(expr)


def escape_xml(value):
    return escape(value, entities={'"': "&quot;"})


def _get_field_expr(index, field):
    if index > 0:
        return "if({field} is null, '', '\\n' + {field})".format(field=field)
    else:
        return "if({field} is null, '', {field})".format(field=field)


def parse_color(color):
    if color.startswith("#"):
        color = color.replace("#", "")
        if len(color) == 3:
            color = "".join(list(map(lambda c: c+c, color)))
        elif len(color) == 6:
            return "#" + color
        return ",".join(list(map(lambda v: str(int(v)), bytearray.fromhex(color))))
    else:
        return _get_color_string(color)


def _get_color_string(color):
    color = color.lower()
    has_alpha = color.startswith("hsla(") or color.startswith("rgba(")
    is_hsl = color.startswith("hsl")
    colors = color.replace("hsla(", "").replace("hsl(", "").replace("rgba(", "").replace("rgb(", "").replace(")", "")\
        .replace(" ", "").replace("%", "").split(",")
    colors = list(map(lambda c: float(c), colors))
    a = 1
    if has_alpha:
        a = colors[3]
    if is_hsl:
        h = colors[0] / 360.0
        s = colors[1] / 100.0
        l = colors[2] / 100.0
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return ",".join(list(map(lambda c: str(int(round(255.0 * c))), [r, g, b, a])))
    else:
        r = colors[0]
        g = colors[1]
        b = colors[2]
        a = round(255.0*a)
        return ",".join(list(map(lambda c: str(int(c)), [r, g, b, a])))


def _apply_scale_range(styles):
    for index, s in enumerate(styles):
        if s["zoom_level"] is None:
            continue

        max_scale_denom = upper_bound_map_scales_by_zoom_level[s["zoom_level"]]
        if index == len(styles) - 1:
            min_scale_denom = 1
        else:
            zoom_of_next = styles[index+1]["zoom_level"]
            min_scale_denom = upper_bound_map_scales_by_zoom_level[zoom_of_next]
        s["min_scale_denom"] = min_scale_denom
        s["max_scale_denom"] = max_scale_denom


def get_properties_by_zoom(paint, property_path, is_color=False, is_expression=False, can_interpolate=False, default=None):
    if (is_color or is_expression) and can_interpolate:
        raise RuntimeError("Colors and expressions cannot be interpolated")

    parts = property_path.split("/")
    value = paint
    for p in parts:
        value = _get_value_safe(value, p)

    stops = None
    if value is not None:
        stops = _get_value_safe(value, "stops")
    else:
        value = default
    properties = []
    if stops:
        base = _get_value_safe(value, "base")
        if not base:
            base = 1
        stops_to_iterate = stops
        if can_interpolate:
            stops_to_iterate = stops[:-1]

        for index, stop in enumerate(stops_to_iterate):
            is_qgis_expr = is_expression
            lower_zoom = stop[0]
            value = stop[1]
            if is_color:
                value = parse_color(value)
            if is_expression:
                value = _parse_expr(value)
            if can_interpolate:
                is_qgis_expr = True
                next_stop = stops[index + 1]
                upper_zoom = next_stop[0]
                second_value = next_stop[1]
                max_scale = upper_bound_map_scales_by_zoom_level[int(lower_zoom)]
                min_scale = upper_bound_map_scales_by_zoom_level[int(upper_zoom)]
                value = "interpolate_exp(get_zoom_for_scale(@map_scale), {base}, {min_zoom}, {max_zoom}, {first_value}, {second_value})"\
                    .format(min_zoom=int(lower_zoom),
                            max_zoom=int(upper_zoom),
                            base=base,
                            min_scale=min_scale,
                            max_scale=max_scale,
                            first_value=value,
                            second_value=second_value)
            properties.append({
                "name": parts[-1],
                "zoom_level": int(lower_zoom),
                "value": value,
                "is_qgis_expr": is_qgis_expr})
    elif value is not None:
        if is_color:
            value = parse_color(value)
        if is_expression:
            value = _parse_expr(value)
        properties.append({
            "name": parts[-1],
            "zoom_level": None,
            "value": value,
            "is_qgis_expr": is_expression})
    return properties


def _get_rules_for_stops(stops):
    rules = []
    for s in stops:
        zoom_level = int(s[0])
        scale = upper_bound_map_scales_by_zoom_level[zoom_level]
        rule = get_qgis_rule(["<=", "@map_scale", scale])
        rules.append({"rule": rule, "value": s[1]})
    return rules


def _get_value_safe(value, path):
    result = None
    if value is not None and isinstance(value, dict) and path and path in value:
        result = value[path]
    return result


def get_qgis_rule(mb_filter, escape_result=True, depth=0):
    op = mb_filter[0]
    if op in _comparision_operators:
        result = _get_comparision_expr(mb_filter)
    elif op in _combining_operators:
        is_none = op == "none"
        all_exprs = map(lambda f: get_qgis_rule(f, escape_result=False, depth=depth+1), mb_filter[1:])
        all_exprs = list(filter(lambda e: e is not None, all_exprs))
        comb_op = _combining_operators[op]
        if comb_op == "and" and len(all_exprs) > 1:
            all_exprs = list(map(lambda e: "({})".format(e), all_exprs))
        full_expr = " {} ".format(comb_op).join(all_exprs)

        if is_none:
            full_expr = "not {}".format(full_expr)
        result = full_expr
    elif op in _membership_operators:
        result = _get_membership_expr(mb_filter)
    elif op in _existential_operators:
        result = _get_existential_expr(mb_filter)
    else:
        raise NotImplementedError("Not Implemented Operator: '{}', Filter: {}".format(op, mb_filter))

    if result:
        # if depth > 0:
        #     result = "({})".format(result)
        if escape_result:
            result = escape_xml(result)
    return result


def _get_comparision_expr(mb_filter):
    assert mb_filter[0] in _comparision_operators
    assert len(mb_filter) == 3
    op = _comparision_operators[mb_filter[0]]
    attr = mb_filter[1]
    value = mb_filter[2]
    if attr == '$type':
        return None
    attr_in_quotes = not attr.startswith("@")
    if attr_in_quotes:
        attr = "\"{}\"".format(attr)
    null_allowed = op == "!="
    if null_allowed:
        null = "{attr} is null or {attr}"
    else:
        null = "{attr} is not null and {attr}"
    attr = null.format(attr=attr)
    return "{attr} {op} '{value}'".format(attr=attr, op=op, value=value)


def _get_membership_expr(mb_filter):
    assert mb_filter[0] in _membership_operators
    assert len(mb_filter) >= 3
    what = "\"{}\"".format(mb_filter[1])
    op = _membership_operators[mb_filter[0]]
    collection = "({})".format(", ".join(list(map(lambda e: "'{}'".format(e), mb_filter[2:]))))
    is_not = mb_filter[0].startswith("!")
    if is_not:
        null_str = "is null or"
    else:
        null_str = "is not null and"
    return "({what} {null} {what} {op} {coll})".format(what=what, op=op, coll=collection, null=null_str)


def _get_existential_expr(mb_filter):
    assert mb_filter[0] in _existential_operators
    assert len(mb_filter) == 2
    op = _existential_operators[mb_filter[0]]
    key = mb_filter[1]
    return "attribute($currentfeature, '{key}') {op}".format(key=key, op=op)
