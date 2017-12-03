import os
import uuid
from xml.sax.saxutils import escape

_join_styles = {
    None: "round",
    "bevel": "bevel",
    "round": "round",
    "miter": "miter"
}

_cap_styles = {
    None: "round",
    "butt": "flat",
    "square": "square",
    "round": "round"
}


def create_style_file(output_directory, layer_style):
    with open(os.path.join(os.path.dirname(__file__), "data/qml_template.xml"), 'r') as f:
        template = f.read()

    layer_type = layer_style["type"]
    rules = []
    symbols = []
    labeling_rules = []

    layer_transparency = 0
    if "layer-transparency" in layer_style:
        layer_transparency = layer_style["layer-transparency"]

    icons_directory = os.path.join(output_directory, "icons")
    for index, s in enumerate(layer_style["styles"]):
        if layer_type == "line":
            rules.append(_get_rule(index, s, rule_content=""))
            symbols.append(_get_line_symbol(index, s))
        elif layer_type == "fill":
            rules.append(_get_rule(index, s, rule_content=""))
            symbols.append(_get_fill_symbol(index, s, icons_directory=icons_directory))
        elif layer_type == "symbol":
            labeling_settings = _get_labeling_settings(s)
            if labeling_settings:
                labeling_rules.append(_get_rule(index, s, rule_content=labeling_settings))
            if "icon-image" in s:
                rules.append(_get_rule(index, s, rule_content=""))
                icn = _get_icon_symbol(index=index,
                                       style=s,
                                       icons_directory=icons_directory,
                                       icon_expr=s["icon-image"])
                symbols.append(icn)


    rule_string = """<rules key="{key}">
    {rules}
    </rules>""".format(key=str(uuid.uuid4()), rules="\n".join(rules))

    symbol_string = """<symbols>
    {symbols}
    </symbols>""".format(symbols="\n".join(symbols))

    renderer = """<renderer-v2 forceraster="0" symbollevels="0" type="RuleRenderer" enableorderby="0">
    {rules}
    {symbols}
  </renderer-v2>
    """.format(rules=rule_string, symbols=symbol_string)

    if not rules:
        renderer = """<renderer-v2 type="nullSymbol"/>"""

    labeling_string = """
    <labeling type="rule-based">
        <rules key="$key$">
            {rules}
        </rules>
    </labeling>
    """.format(rules="\n".join(labeling_rules)).replace("$key$", '{' + str(uuid.uuid4()) + '}')

    template = template.format(renderer=renderer,
                               labeling=labeling_string,
                               layer_transparency=layer_transparency)
    file_path = os.path.join(output_directory, layer_style["file_name"])
    if not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    with open(file_path, 'w') as f:
        f.write(template)


def escape_xml(value):
    return escape(value, entities={'"': "&quot;"})


def _get_labeling_settings(style):
    field_name = _get_value_safe(style, "text-field")
    if not field_name:
        return None

    font = _get_value_safe(style, "text-font", ["Arial"])
    text_transform = _get_value_safe(style, "text-transform", "").lower()
    if text_transform:
        if text_transform == "uppercase":
            text_transform = "upper"
        elif text_transform == "lowercase":
            text_transform = "lower"
        else:
            raise ValueError("Unknown text_transform '{}'".format(text_transform))
        field_name = '{transform}({field})'.format(transform=text_transform, field=field_name)

    if isinstance(font, list):
        font = font[0]
    font = "MS Shell Dlg 2"
    font_size = _get_value_safe(style, "text-size", 16)
    font_size_is_expr = not isinstance(font_size, (int, float))
    font_size_expr_active = "true"
    if not font_size_is_expr:
        font_size_expr = ""
        font_size_expr_active = "false"
        font_size = int(font_size / 96.0 * 72)
    else:
        font_size_expr = "{} / 96*72".format(font_size)
        font_size = ""
    text_color = _get_value_safe(style, "text-color", "0,0,0,255")
    buffer_color = _get_value_safe(style, "text-halo-color", "0,0,0,0")
    buffer_size = _get_value_safe(style, "text-halo-width", 0)
    draw_buffer = 0
    # if buffer_size > 0:
    #     draw_buffer = 1

    label_placement_flags = {
        "line": 9,
        "above": 10
    }

    return """
    <settings>
        <text-style fontItalic="0" fontFamily="{font}" fontLetterSpacing="0" fontUnderline="0" fontWeight="50" fontStrikeout="0" textTransp="0" previewBkgrdColor="#ffffff" fontCapitals="0" textColor="{text_color}" fontSizeInMapUnits="0" isExpression="1" blendMode="0" fontSizeMapUnitScale="0,0,0,0,0,0" fontSize="{font_size}" fieldName="{field_name}" namedStyle="Normal" fontWordSpacing="0" useSubstitutions="0">
            <substitutions/>
        </text-style>
        <text-format placeDirectionSymbol="0" multilineAlign="4294967295" rightDirectionSymbol=">" multilineHeight="1" plussign="0" addDirectionSymbol="0" leftDirectionSymbol="&lt;" formatNumbers="0" decimals="3" wrapChar="" reverseDirectionSymbol="0"/>
        <text-buffer bufferSize="{buffer_size}" bufferSizeMapUnitScale="0,0,0,0,0,0" bufferColor="{buffer_color}" bufferDraw="{draw_buffer}" bufferBlendMode="0" bufferTransp="0" bufferSizeInMapUnits="1" bufferNoFill="0" bufferJoinStyle="128"/>
        <background shapeSizeUnits="1" shapeType="0" shapeSVGFile="" shapeOffsetX="0" shapeOffsetY="0" shapeBlendMode="0" shapeFillColor="255,255,255,255" shapeTransparency="0" shapeSizeMapUnitScale="0,0,0,0,0,0" shapeSizeType="0" shapeJoinStyle="64" shapeDraw="0" shapeBorderWidthUnits="1" shapeSizeX="0" shapeSizeY="0" shapeOffsetMapUnitScale="0,0,0,0,0,0" shapeRadiiX="0" shapeRadiiY="0" shapeOffsetUnits="1" shapeRotation="0" shapeBorderWidth="0" shapeBorderColor="128,128,128,255" shapeRotationType="0" shapeBorderWidthMapUnitScale="0,0,0,0,0,0" shapeRadiiMapUnitScale="0,0,0,0,0,0" shapeRadiiUnits="1"/>
        <shadow shadowOffsetMapUnitScale="0,0,0,0,0,0" shadowOffsetGlobal="1" shadowRadiusUnits="1" shadowTransparency="30" shadowColor="0,0,0,255" shadowUnder="0" shadowScale="100" shadowOffsetDist="1" shadowDraw="0" shadowOffsetAngle="135" shadowRadius="1.5" shadowRadiusMapUnitScale="0,0,0,0,0,0" shadowBlendMode="6" shadowRadiusAlphaOnly="0" shadowOffsetUnits="1"/>
        <placement repeatDistanceUnit="1" placement="3" maxCurvedCharAngleIn="25" repeatDistance="0" distInMapUnits="0" labelOffsetInMapUnits="1" xOffset="0" distMapUnitScale="0,0,0,0,0,0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" preserveRotation="1" repeatDistanceMapUnitScale="0,0,0,0,0,0" centroidWhole="0" priority="5" yOffset="0" offsetType="0" placementFlags="9" centroidInside="0" dist="0" angleOffset="0" maxCurvedCharAngleOut="-25" fitInPolygonOnly="0" quadOffset="4" labelOffsetMapUnitScale="0,0,0,0,0,0"/>
        <rendering fontMinPixelSize="3" scaleMax="10000000" fontMaxPixelSize="10000" scaleMin="1" upsidedownLabels="0" limitNumLabels="0" obstacle="1" obstacleFactor="1" scaleVisibility="0" fontLimitPixelSize="0" mergeLines="1" obstacleType="0" labelPerPart="0" zIndex="0" maxNumLabels="2000" displayAll="0" minFeatureSize="0"/>
        <data-defined>
            <Size expr="{font_size_expr}" field="" active="{font_size_expr_active}" useExpr="{font_size_expr_active}"/>
        </data-defined>
    </settings>
    """.format(font=font,
               font_size=font_size,
               font_size_expr=font_size_expr,
               field_name=field_name,
               text_color=text_color,
               buffer_size=buffer_size,
               buffer_color=buffer_color,
               font_size_expr_active=font_size_expr_active,
               draw_buffer=draw_buffer)


def _get_icon_symbol(index, style, icons_directory, icon_expr):
    opacity = _get_value_safe(style, "fill-opacity", 1)
    svg_path = "'" + os.path.join(icons_directory, "'+{}+'.svg'".format(icon_expr)).replace("\\", "/")
    fallback_path = "'" + os.path.join(icons_directory, "empty.svg'").replace("\\", "/")
    svg_expr = "if_not_exists({svg_path}, {fallback_path})".format(svg_path=svg_path, fallback_path=fallback_path)
    rendering_pass = _get_value_safe(style, "rendering_pass", 0)
    return """<!-- {description} -->
          <symbol alpha="{opacity}" clip_to_extent="1" type="marker" name="{index}">
        <layer pass="{rendering_pass}" class="SvgMarker" locked="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="132,172,217,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="name" v=""/>
          <prop k="name_dd_active" v="1"/>
          <prop k="name_dd_expression" v="{svg_path}"/>
          <prop k="name_dd_field" v=""/>
          <prop k="name_dd_useexpr" v="1"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="17"/>
          <prop k="size_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="size_unit" v="Pixel"/>
          <prop k="vertical_anchor_point" v="1"/>
        </layer>
      </symbol>
    """.format(description=style["name"],
               opacity=opacity,
               svg_path=svg_expr,
               index=index,
               rendering_pass=rendering_pass)


def _get_fill_symbol(index, style, icons_directory):
    opacity = _get_value_safe(style, "fill-opacity", 1)
    offset = list(map(lambda o: str(o), _get_value_safe(style, "fill-translate", default=[0, 0])))
    offset = ",".join(offset)
    fill_color_rgba = _get_value_safe(style, "fill-color", "")
    fill_outline_color_rgba = _get_value_safe(style, "fill-outline-color", fill_color_rgba)
    label = style["name"]
    fill_pattern = _get_value_safe(style, "fill-pattern")
    rendering_pass = _get_value_safe(style, "rendering_pass", 0)
    if style["zoom_level"] is not None:
        label = "{}-zoom-{}".format(label, style["zoom_level"])

    if fill_pattern:
        symbol = _get_fill_pattern_symbol_xml(pattern=fill_pattern,
                                              label=label,
                                              index=index,
                                              opacity=opacity,
                                              rendering_pass=rendering_pass,
                                              icons_directory=icons_directory)
    else:
        symbol = _get_fill_symbol_xml(fill_color_rgba=fill_color_rgba,
                                      fill_outline_color_rgba=fill_outline_color_rgba,
                                      index=index,
                                      label=label,
                                      offset=offset,
                                      opacity=opacity,
                                      rendering_pass=rendering_pass)
    return symbol


def _get_fill_pattern_symbol_xml(pattern, label, index, opacity, rendering_pass, icons_directory):
    svg_path = "'" + os.path.join(icons_directory, "'+{}+'.svg'".format(pattern)).replace("\\", "/")
    fallback_path = "'" + os.path.join(icons_directory, "empty.svg'").replace("\\", "/")
    svg_expr = "if_not_exists({svg_path}, {fallback_path})".format(svg_path=svg_path, fallback_path=fallback_path)
    return """<!-- {description} -->
          <symbol alpha="{opacity}" clip_to_extent="1" type="fill" name="{index}">
        <layer pass="{rendering_pass}" class="SVGFill" locked="0">
          <prop k="angle" v="0"/>
          <prop k="color" v="255,255,255,255"/>
          <prop k="outline_color" v="0,0,0,255"/>
          <prop k="outline_width" v="0.2"/>
          <prop k="outline_width_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="Pixel"/>
          <prop k="pattern_width_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="pattern_width_unit" v="Pixel"/>
          <prop k="svgFile" v=""/>
          <prop k="svgFile_dd_expression" v="{svg_path}"/>
          <prop k="svgFile_dd_active" v="1"/>
          <prop k="svgFile_dd_field" v=""/>
          <prop k="svgFile_dd_useexpr" v="1"/>
          <prop k="svg_outline_width_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="svg_outline_width_unit" v="MM"/>
          <prop k="width" v="17"/>
          <symbol alpha="0" clip_to_extent="1" type="line" name="@3@0">
            <layer pass="0" class="SimpleLine" locked="0">
              <prop k="capstyle" v="square"/>
              <prop k="customdash" v="5;2"/>
              <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
              <prop k="customdash_unit" v="MM"/>
              <prop k="draw_inside_polygon" v="0"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="line_color" v="0,0,0,255"/>
              <prop k="line_style" v="solid"/>
              <prop k="line_width" v="0"/>
              <prop k="line_width_unit" v="MM"/>
              <prop k="offset" v="0"/>
              <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="use_custom_dash" v="0"/>
              <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
            </layer>
          </symbol>
        </layer>
      </symbol>""".format(description=label,
                          opacity=opacity,
                          index=index,
                          svg_path=svg_expr,
                          rendering_pass=rendering_pass)


def _get_fill_symbol_xml(fill_color_rgba, fill_outline_color_rgba, index, label, offset, opacity, rendering_pass):
    symbol = """<!-- {description} -->
        <symbol alpha="{opacity}" clip_to_extent="1" type="fill" name="{index}">
                <layer pass="{rendering_pass}" class="SimpleFill" locked="0">
                    <prop k="border_width_map_unit_scale" v="0,0,0,0,0,0"/>
                    <prop k="color" v="{fill_color}"/>
                    <prop k="joinstyle" v="bevel"/>
                    <prop k="offset" v="{offset}"/>
                    <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
                    <prop k="offset_unit" v="Pixel"/>
                    <prop k="outline_color" v="{fill_outline_color}"/>
                    <prop k="outline_style" v="solid"/>
                    <prop k="outline_width" v="0.7"/>
                    <prop k="outline_width_unit" v="Pixel"/>
                    <prop k="style" v="solid"/>
                </layer>
            </symbol>
            """.format(opacity=opacity,
                       index=index,
                       fill_color=fill_color_rgba,
                       fill_outline_color=fill_outline_color_rgba,
                       offset=offset,
                       description=label,
                       rendering_pass=rendering_pass)
    return symbol


def _get_line_symbol(index, style):
    color = _get_value_safe(style, "line-color")
    width = _get_value_safe(style, "line-width", 1)
    width_expr = width
    width_is_expr = not isinstance(width, (int, float))
    width_dd_active = 0
    if width_is_expr:
        width = "1"
        width_dd_active = 1
    else:
        width_expr = "1"
    capstyle = _cap_styles[_get_value_safe(style, "line-cap")]
    joinstyle = _join_styles[_get_value_safe(style, "line-join")]
    opacity = _get_value_safe(style, "line-opacity", 1)
    dashes = _get_value_safe(style, "line-dasharray", None)
    dash_string = "0;0"
    dash_expr = ""
    use_custom_dash = 0
    if dashes:
        use_custom_dash = 1
        dash = "({} * {})".format(dashes[0], width)
        space = "({} * {})".format(dashes[1], width)
        if space <= width:
            space = "({} + {})".format(space, width)
        dash_expr = "concat({}, ';', {})".format(dash, space)

    label = style["name"]
    if style["zoom_level"] is not None:
        label = "{}-zoom-{}".format(label, style["zoom_level"])
    symbol = """<!-- {description} -->
    <symbol alpha="{opacity}" clip_to_extent="1" type="line" name="{index}">
        <layer pass="{rendering_pass}" class="SimpleLine" locked="0">
          <prop k="capstyle" v="{capstyle}"/>
          <prop k="customdash_dd_expression" v="{dash_expr}"/>
          <prop k="customdash_dd_useexpr" v="{use_custom_dash}"/>
          <prop k="customdash" v="{custom_dash}"/>
          <prop k="customdash_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="use_custom_dash" v="{use_custom_dash}"/>
          <prop k="customdash_unit" v="Pixel"/>
          <prop k="draw_inside_polygon" v="0"/>
          <prop k="joinstyle" v="{joinstyle}"/>
          <prop k="line_color" v="{line_color}"/>
          <prop k="line_style" v="solid"/>
          <prop k="line_width" v="{line_width}"/>
          <prop k="line_width_unit" v="Pixel"/>
          <prop k="width_dd_active" v="{width_dd_active}"/>
          <prop k="width_dd_expression" v="{line_width_expr}"/>
          <prop k="offset" v="0"/>
          <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
          <prop k="offset_unit" v="Pixel"/>
          <prop k="width_map_unit_scale" v="0,0,0,0,0,0"/>
        </layer>
      </symbol>
      """.format(index=index,
                 width_dd_active=width_dd_active,
                 line_width=width,
                 line_width_expr=width_expr,
                 opacity=opacity,
                 line_color=color,
                 capstyle=capstyle,
                 joinstyle=joinstyle,
                 use_custom_dash=use_custom_dash,
                 custom_dash=dash_string,
                 dash_expr=dash_expr,
                 description=label,
                 rendering_pass=style["rendering_pass"])
    return symbol


def _get_rule(index, style, rule_content):
    rule_key = str(uuid.uuid4())
    max_denom = ""
    min_denom = ""
    rule_filter = ""
    label = style["name"]
    if style["zoom_level"] is not None:
        label = "{}-zoom-{}".format(label, style["zoom_level"])
    if style["rule"]:
        rule_filter = 'filter="{}"'.format(style["rule"])

    max_denom_value = _get_value_safe(style, "max_scale_denom")
    min_denom_value = _get_value_safe(style, "min_scale_denom")

    if style["zoom_level"]:
        if max_denom_value is None:
            raise RuntimeError("max denom missing: {}".format(style))
        assert max_denom_value is not None
        assert min_denom_value is not None

    if max_denom_value is not None:
        max_denom = ' scalemaxdenom="{}"'.format(max_denom_value)
    if min_denom_value is not None:
        min_denom = ' scalemindenom="{}"'.format(min_denom_value)

    rule = """<rule key="$key$" {filter} symbol="{symbol}"{max_denom}{min_denom} label="{label}" description="{label}">
    {rule_content}
    </rule>
    """.format(max_denom=max_denom,
               min_denom=min_denom,
               symbol=index,
               label=label,
               filter=rule_filter,
               rule_content=rule_content).replace("$key$", '{' + rule_key + '}')
    return rule


def _get_value_safe(obj, key, default=None):
    result = default
    if key in obj:
        result = obj[key]
    return result
