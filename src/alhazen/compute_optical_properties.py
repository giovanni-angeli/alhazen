# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-fstring-interpolation

import logging

import os
import numpy as np

# local modules from "optical"
import alhazen.ScatteringMatrix

class Material:
    '''
    material is what a layer is made of
    '''

    REFRACTIVE_INDEX_DIR = '' # to be prepended to the filename of the
                              # material needed by _refractive_index_read

    def __init__(self, material):
        self.name = material['name']
        self.fname = material['fname']
        self.description = material['description']
        self.refractive_index = self._refractive_index_read()
        self.wl_range = self._wl_range_get

    def _refractive_index_read(self):
        '''
        read the file containing the refractive index (real and imaginary
        parts) for a given material
        '''
        # open os.path.join(REFRACTIVE_INDEX_DIR,self.fname)
        # read data into refractive_index
        refractive_index = 0

        return refractive_index

    def _wl_range_get(self):
        # from self.refractive_index find min and max for wl_nr, wl_ni
        [ [wl_nr_min, wl_nr_max], [wl_ni_min, wl_ni_max] ] = [ [0,0], [0,0] ]
        return [ [wl_nr_min, wl_nr_max], [wl_ni_min, wl_ni_max] ]


class Layer:

    '''
    layer is the basic element of a structure
    '''

    def __init__(self, json_layer):
        self.name = json_layer['name']
        self.fname = json_layer['fname']
        self.active = json_layer['active']
        self.material = []
        for material in json_layer['materials']:
            self.material.append( Material(material) )
        self.thickness = json_layer['thickness']
        self.coherence = json_layer['coherence']
        self.roughness = json_layer['roughness']

    def refractive_index(self):
        '''
        compute the refractive index of the layer applying the Effective
        Material Approximation (EMA) on a wavelength grid wich is the
        intersection of all the wavelength grids of the materials.
        '''

    def _EMA(self):
        pass

    def _common_wl_grid(self):
        '''
        given the list of wls (both for nr and ni)
        computes the two arrays which is the union of the lists of nr and
        ni, respectively + global min and max value
        '''


class Structure:

    '''
    structure is an array of layers
    '''

    DEFAULT_NP = 400 # needed to build the wavelength grid on which to
                     # compute RT

    def __init__(self, json_structure, params):
        self.layer = []
        for layer in json_structure['layers']:
            self.layer.append( Layer(layer) )

        # get params

    def compute_RT(self):
        R = 0
        T = 0
        return R, T

    def _grid(self):
        pass


def compute_RT( json_structure, params ):

    structure = Structure( json_structure, params )

    R, T = structure.compute_RT()

    return R, T


def get_description(_structure, params):

    message = f"params: {params}<br/>"
    message += "layers: "
    for k, v in _structure.get('structure', {}).items():
        message += f"{k} {v.get('thickness')}(µ), "

    return message
