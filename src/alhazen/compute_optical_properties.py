# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-fstring-interpolation

#import logging

import os

import math
import random
import numpy as np

#import alhazen.ScatteringMatrix

FAKE = True
DEBUG = False

DEFAULT_WL_RANGE = '200,1200'
DEFAULT_NP = 400
DEFAULT_THICKNESS_AL = -1

HERE = os.path.dirname(os.path.abspath(__file__))
MATERIAL_REFRACTIVE_INDEX_DIR = os.path.join(HERE,'..','..','refractive_index_collection')

class Layer:

    '''
    Layer is the basic element of a Structure
    '''

    def __init__(self, layer):
        self.name = layer['name']
        self.active = layer['active']
        self.material = layer['materials']
        material_fraction_test =  sum([ self.material[i]['fraction'] for i in range( len(self.material) ) ])
        if material_fraction_test != 100:
            # info: material,fraction
            # raise error: not 100%
            pass
        self.material_refractive_index = []
        self.thickness = layer['thickness']
        self.coherence = layer['coherence']
        self.roughness = layer['roughness']

    def refractive_index(self):
        '''
        Computes the refractive index of the layer applying the Effective
        Material Approximation (EMA) on a wavelength grid wich is the
        intersection of all the wavelength grids of the materials.
        '''
        for material in self.material:
            if material['fname']:
                self.material_refractive_index.append( self._material_refractive_index_read(material['fname']) )
        self.wl_grid = self._wl_grid_build()

        # TODO: add interpolazion of self.material_refractive_index onto wl_grid

        ri = []
#        # per ogni punto della griglia
#        for wl in self.wl_grid:
#            nr = []
#            ni = []
#            for material in self.material:
#                # nr.append(), ni.append <- interpola self.material_refractive_index onto self.grid
#                pass
#            # call _EMA(nr,ni)
#            Nr.append( (wl,nr) )
#            Ni.append( (wl,ni) )
#
#            ri.append =  self._EMA()

        return ri

    def _material_refractive_index_read(self,fname):

        # FIXME: encoding may be strange for these files: use some guess tool
        with open( os.path.join(MATERIAL_REFRACTIVE_INDEX_DIR,fname), mode="r", encoding="utf-8" ) as f:

            # WARNING: this is for the "optical" format
            # skip header (fixed number of lines with no particular structure that can be recognised)

            # first record contains the material name (not used)
            #name = next(f)
            next(f)

            # second record contains min and max (global) wavelength
            #wl_min, wl_max = next(f).split() # this should contain the min and max (global) wavelength
            next(f)

            # read real part: wavelength, refractive index
            num_of_recs = int(next(f)) # number of records for the real part
            Nr = []
            for _ in range(num_of_recs):
                wl,ri = next(f).split()
                Nr.append( (float(wl),float(ri)) )

            # read Ni -> [ (wl,nr), ...]
            num_of_recs = int(next(f)) # number of records for the imag part
            Ni = []
            for _ in range(num_of_recs):
                wl,ri = next(f).split()
                Ni.append( (float(wl),float(ri)) )

            return { 'real': Nr, 'imag': Ni }

    def _wl_grid_build(self):
        '''
        Returns the list of wl_n* (for both nr and ni) as the union of the
        lists of wl_nr and wl_ni, respectively + global min and max value,
        where:
        - wl_nr = [ self.material[i].refractive_index['real'][i][0] for i in range() ]
        - wl_ni = [ self.material[i].refractive_index['imag'][i][1] for i in range() ]
        '''
        # extract temporary real and imag parts
        _re = [ self.material_refractive_index[i]['real'] for i in range(len(self.material_refractive_index)) ]
        _im = [ self.material_refractive_index[i]['imag'] for i in range(len(self.material_refractive_index)) ]

        # build grids
        wl_re_range = [ _re[i][j][0] for i in range(len(_re)) for j in range(len(_re[0][0])) ]
        wl_im_range = [ _im[i][j][0] for i in range(len(_im)) for j in range(len(_im[0][0])) ]

        # find global min and max
        wl_global_min = max( wl_re_range + wl_im_range )
        wl_global_max = min( wl_re_range + wl_im_range )

        # add global min and max to grids
        wl_re = wl_re_range + [wl_global_min,wl_global_max]
        wl_im = wl_im_range + [wl_global_min,wl_global_max]

        # TODO: sort and remove dupes

        return wl_re, wl_im

    def _EMA(self):
        '''
        Apply the EMA formula
        '''
        return 0

#    def set_thickness(self,thickness):
#        '''
#        Set self.thickness = thickness (from params) if the layer is active
#        '''
#        #TODO: consider moving this to Structure as the "active layer" is
#        # more a property of the structure than of the layer.
#        if self.active and thickness > 0:
#            self.thickness = thickness
#        else:
#            if thickness <= 0:
#                # TODO: set back form.model_params.thickness to self.thickness
#                pass


class Structure:

    '''
    Structure is an array of Layers
    '''

    DEFAULT_NP = 400 # needed to build the wavelength grid on which to
                     # compute RT

    def __init__(self, structure, params):
        self.name = structure['name']
        self.layer = []
        for layer in structure['layers']:
            self.layer.append( Layer(layer) )
        self.thickness_active_layer = float(params['model_edit_panel'].get('thickness_active_layer', DEFAULT_THICKNESS_AL))
        if not self._check():
            # raise error
            pass

    def _check(self):

        # existence of zero or one active layer only
        if [ self.layer[i].active for i in range( len(self.layer) )].count('True') > 1:
            # info
            # raise error
            pass

        # other possible tests

        return True

    def RT(self, params):
        '''
        Interface to ScatteringMatrix.ComputeRT
        '''
        # - get grid params (range, num_of_points)
        # - prepare grid: self._wl_grid( ... )
        # - prepare list in the form to be used in # ScatteringMatrix.ComputeRT
        # - set_thickness_active_layer
        # - call ScatteringMatrix.ComputeRT( ... )

        # debug
        for layer in self.layer:
            layer.refractive_index()
        return 0,0
        # /debug

    def set_thickness_active_layer(self,thickness):
        '''
        Set the thickness of active layer
        '''
        #for layer in self.layer:
        #    if layer.active: layer.thickness = thickness
        for i in range(len(self.layer)):
            if self.layer[i].active:
                self.layer[i].thickness = thickness

    def _grid(self,num_of_points):
        '''
        Creates a list of wavelength to compute Structure properties on
        '''
        pass


def compute_RT( structure, params ):

    structure = Structure( structure, params )
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
