import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from qgis.testing import unittest

from plugin.style_converter.core import get_qgis_rule


class StyleConverterFilterTests(unittest.TestCase):

    # region comparision filters

    def test_qgis_attribute(self):
        rule = get_qgis_rule(["<=", "@map_scale", "20000"], escape_result=False)
        self.assertEqual("@map_scale is not null and @map_scale <= '20000'", rule)

    def test_eq_filter(self):
        rule = get_qgis_rule(["==", "class", "address"], escape_result=False)
        self.assertEqual("\"class\" is not null and \"class\" = 'address'", rule)

    def test_type_comparision(self):
        rule = get_qgis_rule(["==", "$type", "Polygon"], escape_result=False)
        self.assertIsNone(rule)

    def test_neq_filter(self):
        rule = get_qgis_rule(["!=", "class", "address"], escape_result=False)
        self.assertEqual("\"class\" is null or \"class\" != 'address'", rule)

    def test_leq_filter(self):
        rule = get_qgis_rule(["<=", "class", "address"], escape_result=False)
        self.assertEqual("\"class\" is not null and \"class\" <= 'address'", rule)

    def test_eqgt_filter(self):
        rule = get_qgis_rule([">=", "class", "address"], escape_result=False)
        self.assertEqual("\"class\" is not null and \"class\" >= 'address'", rule)

    def test_gt_filter(self):
        rule = get_qgis_rule([">", "class", "address"], escape_result=False)
        self.assertEqual("\"class\" is not null and \"class\" > 'address'", rule)

    def test_lt_filter(self):
        rule = get_qgis_rule(["<", "class", "address"], escape_result=False)
        self.assertEqual("\"class\" is not null and \"class\" < 'address'", rule)

    # endregion

    # region membership filters

    def test_membership_in(self):
        expr = get_qgis_rule(["in", "class", "city", "cafe", "poi"], escape_result=False)
        self.assertEqual("(\"class\" is not null and \"class\" in ('city', 'cafe', 'poi'))", expr)

    def test_membership_not_in(self):
        expr = get_qgis_rule(["!in", "class", "city", "cafe", "poi"], escape_result=False)
        self.assertEqual("(\"class\" is null or \"class\" not in ('city', 'cafe', 'poi'))", expr)
    # endregion

    # region existential filters

    def test_has(self):
        expr = get_qgis_rule(["has", "name"], escape_result=False)
        self.assertEqual("attribute($currentfeature, 'name') is not null", expr)

    def test_has_not(self):
        expr = get_qgis_rule(["!has", "name"], escape_result=False)
        self.assertEqual("attribute($currentfeature, 'name') is null", expr)

    # endregion

    # region combining filters
    def test_all(self):
        f1 = ["==", "class", "address"]
        f2 = ["!=", "name", "hello world"]
        f3 = [">=", "height", "123"]
        rule = get_qgis_rule(["all", f1, f2, f3], escape_result=False)
        expected = """("class" is not null and "class" = 'address') and ("name" is null or "name" != 'hello world') and ("height" is not null and "height" >= '123')"""
        self.assertEqual(expected, rule)

    def test_any(self):
        f1 = ["==", "class", "address"]
        f2 = ["!=", "name", "hello world"]
        rule = get_qgis_rule(["any", f1, f2], escape_result=False)
        expected = """"class" is not null and "class" = \'address\' or "name" is null or "name" != \'hello world\'"""
        self.assertEqual(expected, rule)

    def test_none(self):
        f1 = ["==", "class", "address"]
        f2 = ["!=", "name", "hello world"]
        rule = get_qgis_rule(["none", f1, f2], escape_result=False)
        expected = """not "class" is not null and "class" = \'address\' and not "name" is null or "name" != \'hello world\'"""
        self.assertEqual(expected, rule)
    # endregion
