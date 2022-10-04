# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-fstring-interpolation

import random
import math
import logging

import os
import numpy as np

# local modules from "optical"
import alhazen.optical_functions
import alhazen.ScatteringMatrix

FAKE_RUN = False

DEFAULT_WL_RANGE = "200,1100" # TODO: ask Emanuele for a proper value
DEFAULT_NP = 400 # TODO: ask Emanuele for a proper value

def convert_structure( json_structure, params ):

    '''
    translate json_structure into "opt" structure: the "multilayer" object
    which is a list of "layer" objects, all defined in optical_functions.py
    (from Centurioni's optical.functions) 
    '''

    # get thickness of active layer from params: to be set at the thickness
    # of active layer, if any
    thickness_active_layer = float( params['model_edit_panel'].get('thickness_active_layer', -1) )

    opt_structure = alhazen.optical_functions.multilayer()
    opt_structure.name = json_structure['name']
    for json_layer in json_structure['layers']:
        name = json_layer['name']
        active = json_layer['active']
        materials = json_layer['materials']
        if json_layer['active'] and thickness_active_layer > 0: # user set this value different from the default which is -1
            thickness = thickness_active_layer
        else:
            thickness = json_layer['thickness']
            # FIXME: thickness_active_layer in form.input must be set to the
            # actual thickness read from structure; TODO: ask Giovanni
        coherence = json_layer['coherence']
        roughness = json_layer['roughness']

        here_ = os.path.dirname(os.path.abspath(__file__))
        refraction_index_collection_prth = os.path.join(here_, '..', '..', 'refraction_index_collection')

        # L'istruzione qui sotto e` ricavata da optical.functions.OpenMultilayer()
        # Domande per Emanuele:
        # 1. perche' alcuni valori sono trasformati in stringhe? (thickness e roughness)
        # 2. le fractions sono numeri? NO: sono stringhe
        # 3. incoherent e` un numero? NO: e` una stringa
        # 4. perche; la thinckness e` /10?
        kw_args = dict(
            name=name,
            file1=os.path.join(refraction_index_collection_prth, materials[0]['fname']),
            file2=os.path.join(refraction_index_collection_prth, materials[1]['fname']),
            file3=os.path.join(refraction_index_collection_prth, materials[2]['fname']),
            fr1=str(materials[0]['fraction']),
            fr2=str(materials[1]['fraction']),
            fr3=str(materials[2]['fraction']),
            thickness=str(thickness/10),
            incoherent="1" if coherence==0 else "0",
            roughness=str(roughness))

        opt_layer = alhazen.optical_functions.layer(**kw_args)

        opt_structure.add(opt_layer)

    return opt_structure


def wl_range( opt_structure, params ):
    wl_min, wl_max = [ float(a) for a in params['plot_edit_panel'].get('wl_range',DEFAULT_WL_RANGE).split(',') ]
    wl_min = max( wl_min, opt_structure.lmin )
    wl_max = min( wl_max, opt_structure.lmax )
    wl_np = int( params['plot_edit_panel'].get('wl_np', DEFAULT_NP) ) # FIXME: questo dovrebbe arrivare gia` come numero e invece e` una stringa!
    wl = np.linspace( wl_min, wl_max, wl_np )

    return wl

def compute_RT( json_structure, params ):

    # json_ to opt_structure
    opt_structure = convert_structure( json_structure, params )

    # from Centurioni's optical.functions: for each opt_structure.layer, add n,k (each with its own wl list) to the opt_structure.layer
    alhazen.optical_functions.EMA(opt_structure)

    # this find the min and max wavelenght of the whole structure and define opt_structure.lmin and opt_structure.lmax
    alhazen.optical_functions.CheckWaveRange(opt_structure)

    # Domanda per Emanuele: ci sono altre chiamate necessarie?

    ## wavelength list to interpolate n,k and compute R,T
    #wl_min, wl_max = [ float(a) for a in params['plot_edit_panel'].get('wl_range',DEFAULT_WL_RANGE).split(',') ]
    #wl_min = max( wl_min, opt_structure.lmin )
    #wl_max = min( wl_max, opt_structure.lmax )
    #wl_np = int( params['plot_edit_panel'].get('wl_np', DEFAULT_NP) ) # FIXME: questo dovrebbe arrivare gia` come numero e invece e` una stringa!
    #wl = np.linspace( wl_min, wl_max, wl_np )
    wl = wl_range( opt_structure, params )

    # get incidence angle in degrees and convert it into radians
    incidence_angle = math.pi/180 * float( params['model_edit_panel']['incidence_angle'] ) # FIXME: questo dovrebbe arrivare gia` come numero e invece e` una stringa!

    if FAKE_RUN:
        thickness_active_layer = float( params['model_edit_panel'].get('thickness_active_layer', -1) ) # FIXME: questo dovrebbe arrivare gia` come numero e invece e` una stringa!
        def _R(i):
            return (0.5 + 0.5 * math.cos(thickness_active_layer * i)) + 5. * random.random()
        def _T(i):
            return (0.5 + 0.5 * math.sin(thickness_active_layer * i)) + 5. * random.random()
        R = [ (i,_R(i)) for i in wl]
        T = [ (i,_T(i)) for i in wl]
    else:
        Ronly,Tonly = alhazen.ScatteringMatrix.ComputeRT( alhazen.optical_functions.PrepareList(opt_structure,wl), wl, incidence_angle )
        # WARNING: ScatteringMatrix.ComputeRT returns two numpy.ndarray with
        # containing R and T only (not the wavelength)

        # prepare output in the required format
        R = []
        for l,r in zip(wl,Ronly.tolist()):
            R.append( (l,r) )

        T = []
        for l,r in zip(wl,Tonly.tolist()):
            T.append( (l,r) )


    return R,T


def get_description(_structure, params):

    message = f"params: {params}<br/>"
#    message += "layers: "
# FIXME: does not show anything
#    for k, v in _structure.get('structure', {}).items():
#        message += f"{k} {v.get('thickness')}(µ), "

    return message

