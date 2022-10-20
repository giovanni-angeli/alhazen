# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-fstring-interpolation

#import logging

import os

import math # for fake run only
import random # for fake run only
import numpy as np # for fake run only

import optical_objects
import alhazen.ScatteringMatrix

FAKE = True
DEBUG = False

DEFAULT_WL_RANGE = '200,1200'
DEFAULT_NP = 400
DEFAULT_THICKNESS_AL = -1

HERE = os.path.dirname(os.path.abspath(__file__))
MATERIAL_REFRACTIVE_INDEX_DIR = os.path.join(HERE,'..','..','refractive_index_collection')

def compute_RT( json_structure, params ):

    structure = Structure( json_structure, params )
    R, T = structure.RT(params)
    if DEBUG:
        print( 'structure: ',vars(structure) )
        for layer in structure.layer:
            print( 'structure.layer: ',vars(layer) )
            print('layer.material_refractive_index: ',layer.material_refractive_index)


    if FAKE:

        # to plot fake until the real is not ready
        def _wl_range(params):
            wl_min, wl_max = [float(a) for a in params['plot_edit_panel'].get(
                'wl_range', DEFAULT_WL_RANGE).split(',')]
            wl_np = int(params['plot_edit_panel'].get('wl_np', DEFAULT_NP))
            wl = np.linspace(wl_min, wl_max, wl_np)
            return wl

        thickness_active_layer = float(params['model_edit_panel'].get('thickness_active_layer',DEFAULT_THICKNESS_AL))
        def _R(i):
            return (0.5 + 0.5 * math.cos(thickness_active_layer * i)) + 5. * random.random()
        def _T(i):
            return (0.5 + 0.5 * math.sin(thickness_active_layer * i)) + 5. * random.random()

        wl = _wl_range(params)
        R = [ (i,_R(i)) for i in wl]
        T = [ (i,_T(i)) for i in wl]

    return R, T


def compute_Chi( structure, experimental_data, params ):
    pass


def get_description(_structure, params):

    message = f"params: {params}<br/>"
    message += "layers: "
    for k, v in _structure.get('structure', {}).items():
        message += f"{k} {v.get('thickness')}(µ), "

    return message
