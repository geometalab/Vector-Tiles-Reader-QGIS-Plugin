import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import get_qgis_rule


#region comparision filters

def test_qgis_attribute():
    rule = get_qgis_rule(["<=", "@map_scale", "20000"], escape_result=False)
    assert rule == "@map_scale is not null and @map_scale <= '20000'"


def test_eq_filter():
    rule = get_qgis_rule(["==", "class", "address"], escape_result=False)
    assert rule == "\"class\" is not null and \"class\" = 'address'"


def test_type_comparision():
    rule = get_qgis_rule(["==", "$type", "Polygon"], escape_result=False)
    assert rule is None


def test_neq_filter():
    rule = get_qgis_rule(["!=", "class", "address"], escape_result=False)
    assert rule == "\"class\" is null or \"class\" != 'address'"


def test_leq_filter():
    rule = get_qgis_rule(["<=", "class", "address"], escape_result=False)
    assert rule == "\"class\" is not null and \"class\" <= 'address'"


def test_eqgt_filter():
    rule = get_qgis_rule([">=", "class", "address"], escape_result=False)
    assert rule == "\"class\" is not null and \"class\" >= 'address'"


def test_gt_filter():
    rule = get_qgis_rule([">", "class", "address"], escape_result=False)
    assert rule == "\"class\" is not null and \"class\" > 'address'"


def test_lt_filter():
    rule = get_qgis_rule(["<", "class", "address"], escape_result=False)
    assert rule == "\"class\" is not null and \"class\" < 'address'"

#endregion

# region membership filters


def test_membership_in():
    expr = get_qgis_rule(["in", "class", "city", "cafe", "poi"], escape_result=False)
    assert expr == "(\"class\" is not null and \"class\" in ('city', 'cafe', 'poi'))"


def test_membership_not_in():
    expr = get_qgis_rule(["!in", "class", "city", "cafe", "poi"], escape_result=False)
    assert expr == "(\"class\" is null or \"class\" not in ('city', 'cafe', 'poi'))"
# endregion

# region existential filters

def test_has():
    expr = get_qgis_rule(["has", "name"], escape_result=False)
    assert expr == "attribute($currentfeature, 'name') is not null"


def test_has_not():
    expr = get_qgis_rule(["!has", "name"], escape_result=False)
    assert expr == "attribute($currentfeature, 'name') is null"

# endregion

# region combining filters
def test_all():
    f1 = ["==", "class", "address"]
    f2 = ["!=", "name", "hello world"]
    f3 = [">=", "height", "123"]
    rule = get_qgis_rule(["all", f1, f2, f3], escape_result=False)
    assert rule == """("class" is not null and "class" = \'address\') and ("name" is null or "name" != \'hello world\') and ("height" is not null and "height" >= \'123\')"""


def test_any():
    f1 = ["==", "class", "address"]
    f2 = ["!=", "name", "hello world"]
    rule = get_qgis_rule(["any", f1, f2], escape_result=False)
    assert rule == """"class" is not null and "class" = \'address\' or "name" is null or "name" != \'hello world\'"""


def test_none():
    f1 = ["==", "class", "address"]
    f2 = ["!=", "name", "hello world"]
    rule = get_qgis_rule(["none", f1, f2], escape_result=False)
    assert rule == """not "class" is not null and "class" = \'address\' and not "name" is null or "name" != \'hello world\'"""
# endregion
