"""
Define new functions using @qgsfunction. feature and parent must always be the
last args. Use args=-1 to pass a list of values as arguments
"""

from qgis.core import *
from qgis.gui import *
import os

def interpolate(a, b, ratio):
    return (a * (1 - ratio)) + (b * ratio)

def get_exponential_interpolation_factor(input, base, lower, upper):
    difference = upper - lower
    progress = input - lower
    if (difference == 0):
        return difference
    elif base == 1:
        return progress / difference
    else:
        ratio = ((base**progress) - 1) / ((base**difference) - 1)
        return ratio

@qgsfunction(args='auto', group='Custom')
def if_not_exists(file_path, default, feature, parent):
	if os.path.isfile(file_path):
		return file_path
	else:
		return default

@qgsfunction(args='auto', group='Custom')
def interpolate_exp(zoom, base, lower_zoom, upper_zoom, lower_value, upper_value, feature, parent):
    ratio = get_exponential_interpolation_factor(zoom, base, lower_zoom, upper_zoom)
    return interpolate(lower_value, upper_value, ratio)

_zoom_level_by_lower_scale_bound = {
    1000000000: 0,
    500000000: 1,
    200000000: 2,
    50000000: 3,
    25000000: 4,
    12500000: 5,
    6500000: 6,
    3000000: 7,
    1500000: 8,
    750000: 9,
    400000: 10,
    200000: 11,
    100000: 12,
    50000: 13,
    25000: 14,
    12500: 15,
    5000: 16,
    2500: 17,
    1500: 18,
    750: 19,
    500: 20,
    250: 21,
    100: 22,
    0: 23
}

def get_zoom(scale, lower_scale, upper_scale, lower_zoom, upper_zoom):
    ratio = float(upper_scale - scale) / (upper_scale - lower_scale)
    zoom = lower_zoom + (upper_zoom - lower_zoom) * ratio
    return zoom

@qgsfunction(args='auto', group='Custom')
def get_zoom_for_scale(scale, feature, parent):
    scale = int(scale)
    scales_sorted = list(reversed(sorted(_zoom_level_by_lower_scale_bound)))
    lower_zoom = None
    upper_zoom = None
    lower_scale = None
    upper_scale = None
    for index, s in enumerate(scales_sorted):
        if scale > s:
            lower_scale = s
            upper_scale = scales_sorted[index+1]
            lower_zoom = _zoom_level_by_lower_scale_bound[upper_scale]
            upper_zoom = _zoom_level_by_lower_scale_bound[lower_scale]
            break
    return get_zoom(scale, lower_scale, upper_scale, lower_zoom, upper_zoom)