# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name

import os
import random
import math

def compute_R(json_structure):

    def f(i):
        return 50. * (0.5 + 0.5 * math.cos(0.005 * i)) + 5. * random.random()

    out_data = [(i, f(i)) for i in range(270, 1100, 2)]

    return out_data 
def compute_T(json_structure):

    def f(i):
        return 50. * (0.5 + 0.5 * math.sin(0.005 * i)) + 5. * random.random()

    out_data = [(i, f(i)) for i in range(270, 1100, 2)]

    return out_data 
