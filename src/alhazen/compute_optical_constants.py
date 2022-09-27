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
# ~ import alhazen.ScatteringMatrix

DEFAULT_NP = 400

def compute_RT(json_structure, params):
    '''
    Computes Reflectance (R) and Transmittance (T) for a given structure (in
    json format) in the range of wave length (wl) defined in params
    '''

    logging.info(f"params:{params}")

    # esempio di estrazione dati da struttura
    # structure is a list of layers; each layer is a dict that includes a
    # list of materials; each material is a dict;

    # examples:
    # layer = json_structure.get('layer') # get the list of layers; each layer is a dict
    # json_structure.get('layer')[0].get('material')[0].get('fname') # get fname of first material of first layer

    layers = json_structure.get('layers') # get the list of layers; each layer is a dict

    # wl range
    wl_np = int( params.get('wl_np', DEFAULT_NP) )
    wl_min,wl_max = [ float(a) for a in params.get('wl_range').split(',') ]
    # TODO: verify wl_min < wl_max
    #if autoRange:
    #   wl_min = max( wl_min, ...) # TODO: put the min wl value read from structure refractiveindex file
    #   wl_max = min( wl_max, ...) # TODO: put the max wl value read from structure refractiveindex file
    wl_range = np.linspace( wl_min, wl_max, wl_np )

    # TODO: process structure to prepare input to ScatteringMatrix.compute_RT
    structure = []
    for l in layers:
        thickness = float( l.get('thickness') )
        #coherence = bool( l.get('coherence') )
        coherence = abs( 1 - int(l.get('coherence')) ) # this is to make it compatible with "optical" functions
        roughness = float( l.get('roughness') )
        materials = l.get('materials')
        # TODO: test sum of material fracts
        # compute refractiveIndex (ni,nr) from materials (if one only: ... else: EMA)
        # interpolate refractiveIndex onto wl
        # structure.append( [thickness, refractiveIndex, coherence, roughness] )

    # altri parametri
    thickness_active_layer = float( params.get('thickness_active_layer') )

    def _R(i):
        return (0.5 + 0.5 * math.cos(thickness_active_layer * i)) + 5. * random.random()
    def _T(i):
        return (0.5 + 0.5 * math.sin(thickness_active_layer * i)) + 5. * random.random()

    R = [ (i,_R(i)) for i in wl_range]
    T = [ (i,_T(i)) for i in wl_range]

    return R,T


def get_description(_structure, params):

    message = f"params: {params}<br/>"
    #message += "layers: "
    #for k, v in _structure.get('structure', {}).items():
    #    message += f"{k} {v.get('thickness')}(µ), "
    #message = f"layers: {_structure.get('layers')}"

    return message
