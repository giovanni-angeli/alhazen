# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name

import os
import random

def compute_R(json_structure):

    out_data = [(i, .3 + i + .3 * random.random()) for i in range(100)]
    return out_data 

def compute_T(json_structure):

    out_data = [(i, .1 + i + .2 * random.random()) for i in range(100)]
    return out_data 
