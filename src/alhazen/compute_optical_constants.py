# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-fstring-interpolation

import random
import math
import logging

import numpy as np

# local modules from "optical"
import alhazen.optical_functions
import alhazen.ScatteringMatrix

DEFAULT_NP = 400

def compute_RT(json_structure, params):
    '''
    Computes Reflectance (R) and Transmittance (T) for a given structure (in
    json format) in the range of wave length (wl) defined in params
    '''

    logging.info(f"params:{params}")

    # estrazione dati da struttura e parametri
    #fraction1 = json_structure.get('structure', {}).get("TopMedium", {}).get("fraction1", 30)
    #fraction1 = float(fraction1)

    thickness_active_layer = float( params.get('thickness_active_layer') )


    # wl range
    wl_np = int( params.get('wl_np', DEFAULT_NP) )
    wl_min,wl_max = [ float(a) for a in params.get('wl_range').split(',') ]
    # TODO: verify wl_min < wl_max
    #if autoRange:
    #   wl_min = max( wl_min, ...) # TODO: put the min wl value read from structure refractiveindex file
    #   wl_max = min( wl_max, ...) # TODO: put the max wl value read from structure refractiveindex file
    wl_range = np.linspace( wl_min, wl_max, wl_np )

    # TODO: process structure to prepare input to ScatteringMatrix.compute_RT
    # structure_processed = []
    # for layer in structure
    #   get thickness, coherence, roughness, refractive_index
    #   interpolate refractive_index onto wl
    #   structure_processed.append(....)

    def _R(i):
        return (0.5 + 0.5 * math.cos(thickness_active_layer * i)) + 5. * random.random()
    def _T(i):
        return (0.5 + 0.5 * math.sin(thickness_active_layer * i)) + 5. * random.random()

    R = [ (i,_R(i)) for i in wl_range]
    T = [ (i,_T(i)) for i in wl_range]

    return R,T


def get_description(_structure, params):

    message = f"params: {params}<br/>"
    message += "layers: "
    for k, v in _structure.get('structure', {}).items():
        message += f"{k} {v.get('thickness')}(µ), "

    return message
