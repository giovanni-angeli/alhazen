# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-fstring-interpolation

import logging

import os
import numpy as np

import alhazen.ScatteringMatrix

MATERIAL_REFRACTIVE_INDEX_DIR = '.'

class Layer:

    '''
    Layer is the basic element of a Structure
    '''

    def __init__(self, json_layer):
        self.name = json_layer['name']
        self.active = json_layer['active']
        self.material = json_layer['materials']
        material_fraction_test =  sum([ material[i]['fraction'] for i in range( len(material) ) ])
        if material_fraction_test != 100:
            # info: material,fraction
            # raise error: not 100%
            pass
        self.thickness = json_layer['thickness']
        self.coherence = json_layer['coherence']
        self.roughness = json_layer['roughness']

    def refractive_index(self):
        '''
        Computes the refractive index of the layer applying the Effective
        Material Approximation (EMA) on a wavelength grid wich is the
        intersection of all the wavelength grids of the materials.
        '''
        # call _material_refractive_index_read(material['fname']) for material in self.material
        # define wavelength ranges and "grid" (_wl_grid)
        # interpolate refractive indices onto wl_grid
        # apply EMA formul
        #  ... see optical.functions.EMA for details
        pass

    def set_thickness(self,thickness):
        '''
        Set self.thickness = thickness (from params) if the layer is active
        '''
        #TODO: consider moving this to Structure as the "active layer" is
        # more a property of the structure than of the layer.
        if self.active and thickness > 0:
            self.thickness = thickness
        else:
            if thickness <= 0:
                # set back form.model_params.thickness to self.thickness
                pass
        pass

    def _material_refractive_index_read(fname):
        # open file fname
        # read Nr -> [ (wl,nr), ...]
        # read Ni -> [ (wl,nr), ...]
        # return { 'real': Nr, 'imag': Ni } or set
        #     self.material[i].refractive_index = { 'real': Nr, 'imag': Ni }
        #     boh!
        pass

    def _wl_grid(self):
        '''
        Returns the list of wl_n* (for both nr and ni) as the union of the
        lists of wl_nr and wl_ni, respectively + global min and max value,
        where:
        - wl_nr = [ self.material[i].refractive_index['real'][i][0] for i in range() ]
        - wl_ni = [ self.material[i].refractive_index['imag'][i][1] for i in range() ]
        '''
        pass

    def _EMA(self):
        '''
        Apply the EMA formula
        '''
        pass


class Structure:

    '''
    Structure is an array of Layers
    '''

    DEFAULT_NP = 400 # needed to build the wavelength grid on which to
                     # compute RT

    def __init__(self, json_structure, params):
        self.name = json_structure['name']
        self.layer = []
        for layer in json_structure['layers']:
            self.layer.append( Layer(layer) )

    def _check(self):

        # existence of zero or one active layer only
        if self.layer[:].active.count('True') > 1:
            # raise error
            pass

    def compute_RT(self):
        '''
        Interface to ScatteringMatrix.ComputeRT
        '''

    def set_thickness_active_layer(self,thickness)
        '''
        Set the thickness of active layer
        '''
        #for layer in self.layer:
        #    if layer.active: layer.thickness = thickness
        for i in range(len(self.layer)):
            if self.layer[i].active: self.layer[i].thickness = thickness

    def _grid(self, np):
        '''
        Creates a list of wavelength to compute Structure properties on
        '''
        pass


def compute_RT( json_structure, params ):

    structure = Structure( json_structure, params )

    R, T = structure.compute_RT()

    return R, T


def compute_Chi( json_structure, experimental_data, params )
    pass
    

def get_description(_structure, params):

    message = f"params: {params}<br/>"
    message += "layers: "
    for k, v in _structure.get('structure', {}).items():
        message += f"{k} {v.get('thickness')}(µ), "

    return message
