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

    # structure is a list of layers; each layer is a dict that includes a
    # list of materials; each material is a dict;
    layers = json_structure.get('layers') # get the list of layers; each layer is a dict

    # wl range
    wl_min,wl_max = [ float(a) for a in params.get('plot_edit_panel').get('wl_range').split(',') ]
    # TODO: verify wl_min < wl_max

    # TODO:
    #if autoRange:
    #   wl_min = min wl value read from structure refractiveindex file
    #   wl_max = max wl value read from structure refractiveindex file
    #else:
    #   wl_min,wl_max = [ float(a) for a in params.get('wl_range').split(',') ]
    #   wl_min = max( wl_min, ...) # TODO: put the min wl value read from structure refractiveindex file
    #   wl_max = min( wl_max, ...) # TODO: put the max wl value read from structure refractiveindex file
    wl_np = int( params.get('plot_edit_panel').get('wl_np', DEFAULT_NP) )
    wl = np.linspace( wl_min, wl_max, wl_np )

    # TODO: prepare structure  as input to ScatteringMatrix.compute_RT
    structure = []
    for layer in layers:
        thickness = float( layer.get('thickness') )
        #coherence = bool( layer.get('coherence') )
        incoherence = abs( 1 - int(layer.get('coherence')) ) # this is to make it compatible with "optical" functions that use incoherence (!?)
        roughness = float( layer.get('roughness') )
        materials = layer.get('materials')
        # TODO: test sum of material fracts
        #refractive_index = EMA(materials)
        # interpolate refractive_index onto wl
        #structure.append( [thickness, refractive_index, incoherence, roughness] )

    # altri parametri
    # FIXME: forse la thickness of active layer va impostata qui come la
    # thickness di uno dei layer calcolati sopra. come definire active layer
    # nella struttura? chiedere Emanuele.
    thickness_active_layer = float( params.get('model_edit_panel').get('thickness_active_layer') )
    incidence_angle = float( params.get('model_edit_panel').get('incidence_angle') )

    def _R(i):
        return (0.5 + 0.5 * math.cos(thickness_active_layer * i)) + 5. * random.random()
    def _T(i):
        return (0.5 + 0.5 * math.sin(thickness_active_layer * i)) + 5. * random.random()

    # ComputeRT da ScatteringMatrix.py
    # R,T = ComputeRT(structure, wl, incidence_angle)

    R = [ (i,_R(i)) for i in wl]
    T = [ (i,_T(i)) for i in wl]

    return R,T


def get_description(_structure, params):

    message = f"params: {params}<br/>"
#    message += "layers: "
# FIXME: does not show anything
#    for k, v in _structure.get('structure', {}).items():
#        message += f"{k} {v.get('thickness')}(µ), "

    return message

