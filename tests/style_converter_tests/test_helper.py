from plugin.style_converter.core import get_styles, parse_color, get_qgis_rule, get_background_color, xml_helper, _get_match_expr
from qgis.testing import unittest


class StyleConverterHelperTests(unittest.TestCase):

    def test_parse_rgb(self):
        rgba = parse_color("rgb(1,2,3)")
        self.assertEqual("1,2,3,255", rgba)

    def test_parse_rgba(self):
        rgba = parse_color("rgba(1, 2, 3, 0.5)")
        self.assertEqual("1,2,3,128", rgba)

    def test_parse_hsl(self):
        rgba = parse_color("hsl(28, 76%, 67%)")
        self.assertEqual("235,167,107,255", rgba)

    def test_parse_hsla(self):
        rgba = parse_color("hsla(28, 76%, 67%, 0.5)")
        self.assertEqual("235,167,107,128", rgba)

    def test_parse_color_match(self):
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
        expected = """if ("type" is not null and "type" = 'Air Transport', '#e6e6e6', if ("type" is not null and "type" = 'Education', '#f7eaca', '235,167,107,128'))"""
        self.assertEqual(expected, rgba)

    def test_parse_hex_alpha(self):
        rgba = parse_color("#ffff0c32")
        self.assertEqual("255,255,12,50", rgba)

    def test_parse_hex(self):
        rgba = parse_color("#ffff0c")
        self.assertEqual("#ffff0c", rgba)

    def test_parse_short_hex(self):
        rgba = parse_color("#abc")
        self.assertEqual("170,187,204", rgba)

    def test_line_dasharray(self):
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
        self.assertTrue(True)

    def test_line_dasharray_multiple(self):
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
        self.assertTrue(True)

    def test_line_cap(self):
        style = {
            "id": None,
            "type": "line",
            "layout": {
                "line-cap": "round",
                "line-join": "square"
            }
        }
        styles = get_styles(style)
        self.assertEqual(1, len(styles))
        self.assertEqual("square", styles[0]["line-join"])
        self.assertEqual("round", styles[0]["line-cap"])

    def test_stops(self):
        style = _get_line_layer({
            "line-color": "#9e9cab",
            "line-dasharray": [3, 1, 1, 1],
            "line-width": {
                "base": 1.4,
                "stops": [[4, 0.4], [5, 1], [12, 3]]}
        })
        styles = get_styles(style)
        self.assertTrue(True)

    def test_zoom_level_zero(self):
        style = _get_fill_style({
            "fill-opacity": {
                "base": 1,
                "stops": [[0, 0.9], [10, 0.3]]
            }
        })
        styles = get_styles(style)
        self.assertEqual(2, len(styles))
        expected = {
            'zoom_level': 0,
            'max_scale_denom': 1000000000,
            'min_scale_denom': 750000,
            'fill-color': '0,0,0,0',
            'fill-opacity': 0.9
        }
        self.assertDictEqual(expected, styles[0])

    def test_get_styles_float(self):
        style = _get_fill_style({
            "fill-opacity": 0.7,
            "fill-color": "#f2eae2",
        })
        styles = get_styles(style)
        expected = {
            "fill-color": "#f2eae2",
            "fill-opacity": 0.7,
            "zoom_level": None,
            "min_scale_denom": None,
            "max_scale_denom": None
        }
        self.assertDictEqual(expected, styles[0])

    def test_get_background_color(self):
        layer = """{"layers": [{
          "id": "background",
          "type": "background",
          "paint": {
            "background-color": "#f8f4f0"
          }
        }]}"""
        color = get_background_color(layer)
        self.assertEqual("#f8f4f0", color)

    def test_get_styles_simple(self):
        style = _get_fill_style({
            "fill-outline-color": "#dfdbd7",
            "fill-color": "#f2eae2",
        })
        styles = get_styles(style)
        self.assertEqual(1, len(styles))
        expected = {
            "fill-outline-color": "#dfdbd7",
            "fill-color": "#f2eae2",
            "zoom_level": None,
            "min_scale_denom": None,
            "max_scale_denom": None
        }
        self.assertDictEqual(expected, styles[0])

    def test_highway_motorway(self):
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
        self.assertEqual(2, len(result))

    def test_scale(self):
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
        self.assertEqual(1, len(styles))
        self.assertEqual(10, styles[0]["zoom_level"])

    def test_get_styles(self):
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
        styles = sorted(styles, key=lambda s: s["zoom_level"])
        self.assertEqual(2, len(styles))
        first_expected = {
            'fill-outline-color': '#dfdbd7',
            'fill-color': '#f2eae2',
            'zoom_level': 13,
            'fill-opacity': 0,
            'max_scale_denom': 100000,
            'min_scale_denom': 12500
        }
        second_expected = {
            'fill-outline-color': '#dfdbd7',
            'fill-color': '#f2eae2',
            'zoom_level': 16,
            'fill-opacity': 1,
            'max_scale_denom': 12500,
            'min_scale_denom': 1
        }
        self.assertDictEqual(first_expected, styles[0])
        self.assertDictEqual(second_expected, styles[1])

    def test_filter_depth(self):
        highway_primary_casing = get_qgis_rule(_highway_primary_casing, escape_result=False)
        highway_primary = get_qgis_rule(_highway_primary, escape_result=False)
        self.assertEqual(highway_primary, highway_primary_casing)


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
