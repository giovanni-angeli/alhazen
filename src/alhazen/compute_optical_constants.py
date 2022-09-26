# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-fstring-interpolation

import random
import math
import logging


def compute_R(json_structure, params):

    logging.info(f"params:{params}")

    fraction1 = json_structure.get('structure', {}).get("TopMedium", {}).get("fraction1", 30)
    fraction1 = float(fraction1)
    thickness_active_layer = params.get('thickness_active_layer', 0)
    thickness_active_layer = float(thickness_active_layer) * .001

    def f(i):
        return fraction1 * (0.5 + 0.5 * math.cos(thickness_active_layer * i)) + 5. * random.random()

    out_data = [(i, f(i)) for i in range(270, 1100, 2)]

    return out_data


def compute_T(json_structure, params):

    logging.info(f"params:{params}")

    fraction1 = json_structure.get('structure', {}).get("TopMedium", {}).get("fraction1", 30)
    fraction1 = float(fraction1)
    thickness_active_layer = params.get('thickness_active_layer', 0)
    thickness_active_layer = float(thickness_active_layer) * .001

    def f(i):
        return fraction1 * (0.5 + 0.5 * math.sin(thickness_active_layer * i)) + 5. * random.random()

    out_data = [(i, f(i)) for i in range(270, 1100, 2)]

    return out_data


def get_description(_structure, params):

    message = f"params: {params}<br/>"
    message += "layers: "
    for k, v in _structure.get('structure', {}).items():
        message += f"{k} {v.get('thickness')}(µ), "

    return message
