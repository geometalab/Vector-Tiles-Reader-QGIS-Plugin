from core import get_styles, parse_color, get_qgis_rule, get_background_color, xml_helper, _get_match_expr


def test_parse_rgb():
    rgba = parse_color("rgb(1,2,3)")
    assert rgba == "1,2,3,255"


def test_parse_rgba():
    rgba = parse_color("rgba(1, 2, 3, 0.5)")
    assert rgba == "1,2,3,128"


def test_parse_hsl():
    rgba = parse_color("hsl(28, 76%, 67%)")
    assert rgba == "235,167,107,255"


def test_parse_hsla():
    rgba = parse_color("hsla(28, 76%, 67%, 0.5)")
    assert rgba == "235,167,107,128"


def test_parse_color_match():
    rgba = parse_color([
        "match",
        [
            "get",
            "type"
        ],
        "Air Transport",
        "#e6e6e6",
        "Education",
        "#f7eaca",
        "hsla(28, 76%, 67%, 0.5)"
    ])
    assert rgba == """if ("type" is not null and "type" = 'Air Transport', '#e6e6e6', if ("type" is not null and "type" = 'Education', '#f7eaca', '235,167,107,128'))"""


def test_parse_hex_alpha():
    rgba = parse_color("#ffff0c32")
    assert rgba == "255,255,12,50"


def test_parse_hex():
    rgba = parse_color("#ffff0c")
    assert rgba == "#ffff0c"


def test_parse_short_hex():
    rgba = parse_color("#abc")
    assert rgba == "170,187,204"


def test_line_dasharray():
    style = _get_line_layer({
        "line-color": "#cba",
        "line-dasharray": [
            1.5,
            0.75
        ],
        "line-width": {
            "base": 1.2,
            "stops": [
                [
                    15,
                    1.2
                ],
                [
                    20,
                    4
                ]
            ]
        }
    })
    styles = get_styles(style)


def test_line_dasharray_multiple():
    layer = _get_line_layer({
        "id": "test",
        "line-dasharray": [
            5,
            6,
            10,
            11
        ]
    })
    styles = get_styles(layer)
    d = xml_helper._get_line_symbol(0, styles[0])
    a = ""


def test_line_cap():
    style = {
        "id": None,
        "type": "line",
        "layout": {
            "line-cap": "round",
            "line-join": "square"
        }
    }
    styles = get_styles(style)
    assert len(styles) == 1
    assert styles[0]["line-join"] == "square"
    assert styles[0]["line-cap"] == "round"


def test_stops():
    style = _get_line_layer({
        "line-color": "#9e9cab",
        "line-dasharray": [3, 1, 1, 1],
        "line-width": {
            "base": 1.4,
            "stops": [[4, 0.4], [5, 1], [12, 3]]}
    })
    styles = get_styles(style)


def test_zoom_level_zero():
    style = _get_fill_style({
        "fill-opacity": {
            "base": 1,
            "stops": [[0, 0.9], [10, 0.3]]
        }
    })
    styles = get_styles(style)
    assert len(styles) == 2
    assert _are_dicts_equal(styles[0], {
        'zoom_level': 0,
        'max_scale_denom': 1000000000,
        'min_scale_denom': 750000,
        'fill-color': '0,0,0,0',
        'fill-opacity': 0.9
    })

    assert _are_dicts_equal(styles[1], {
        'zoom_level': 10,
        'max_scale_denom': 750000,
        'min_scale_denom': 1,
        'fill-color': '0,0,0,0',
        'fill-opacity': 0.3
    })


def test_get_styles_float():
    style = _get_fill_style({
        "fill-opacity": 0.7,
        "fill-color": "#f2eae2",
    })
    styles = get_styles(style)
    assert styles[0] == {
        "fill-color": "#f2eae2",
        "fill-opacity": 0.7,
        "zoom_level": None,
        "min_scale_denom": None,
        "max_scale_denom": None
    }


def test_get_background_color():
    layer = """{"layers": [{
      "id": "background",
      "type": "background",
      "paint": {
        "background-color": "#f8f4f0"
      }
    }]}"""
    color = get_background_color(layer)
    assert color == "#f8f4f0"


def test_get_styles_simple():
    style = _get_fill_style({
        "fill-outline-color": "#dfdbd7",
        "fill-color": "#f2eae2",
    })
    styles = get_styles(style)
    assert len(styles) == 1
    assert styles[0] == {
        "fill-outline-color": "#dfdbd7",
        "fill-color": "#f2eae2",
        "zoom_level": None,
        "min_scale_denom": None,
        "max_scale_denom": None
    }


def test_highway_motorway():
    style = _get_line_layer({
        "line-width": {
            "base": 1.2,
            "stops": [
                [
                    6.5,
                    0
                ],
                [
                    7,
                    0.5
                ],
                [
                    20,
                    18
                ]
            ]
        }
    })
    result = get_styles(style)
    assert len(result) == 2


def test_scale():
    style = _get_line_layer({
        "line-width": {
            "stops": [
                [
                    10,
                    0
                ],
                [
                    15,
                    1
                ]
            ]
        }
    })
    styles = get_styles(style)
    assert len(styles) == 1
    assert styles[0]["zoom_level"] == 10


def test_get_styles():
    style = _get_fill_style({
        "fill-outline-color": "#dfdbd7",
        "fill-color": "#f2eae2",
        "fill-opacity": {
            "base": 1,
            "stops": [
                [
                    13,
                    0
                ],
                [
                    16,
                    1
                ]
            ]
        }
    })
    styles = get_styles(style)
    assert len(styles) == 2
    styles = sorted(styles, key=lambda s: s["zoom_level"])
    assert _are_dicts_equal(styles[0], {
        'fill-outline-color': '#dfdbd7',
        'fill-color': '#f2eae2',
        'zoom_level': 13,
        'fill-opacity': 0,
        'max_scale_denom': 100000,
        'min_scale_denom': 12500
    })
    assert _are_dicts_equal(styles[1], {
        'fill-outline-color': '#dfdbd7',
        'fill-color': '#f2eae2',
        'zoom_level': 16,
        'fill-opacity': 1,
        'max_scale_denom': 12500,
        'min_scale_denom': 1
    })


def test_filter_depth():
    highway_primary_casing = get_qgis_rule(_highway_primary_casing, escape_result=False)
    highway_primary = get_qgis_rule(_highway_primary, escape_result=False)
    assert highway_primary_casing == highway_primary


_highway_primary_casing = [
    "all",
    [
        "!in",
        "brunnel",
        "bridge",
        "tunnel"
    ],
    [
        "in",
        "class",
        "primary"
    ]
]

_highway_primary = [
    "all",
    [
        "==",
        "$type",
        "LineString"
    ],
    [
        "all",
        [
            "!in",
            "brunnel",
            "bridge",
            "tunnel"
        ],
        [
            "in",
            "class",
            "primary"
        ]
    ]
]


def _are_dicts_equal(d1, d2):
    for k in d1:
        if k not in d2:
            raise AssertionError("Key '{}' not in d2: {}".format(k, d2))
    for k in d2:
        if k not in d1:
            raise AssertionError("Key '{}' not in d1: {}".format(k, d1))
    for k in d1:
        if d1[k] != d2[k]:
            raise AssertionError("Key '{}' not equal: {} != {}".format(k, d1[k], d2[k]))
    return True


def _get_fill_style(paint):
    return {
        "id": None,
        "type": "fill",
        "paint": paint
    }


def _get_line_layer(paint):
    return {
        "id": None,
        "type": "line",
        "paint": paint
    }
