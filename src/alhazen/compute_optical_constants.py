# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-fstring-interpolation

import math
import logging

import os
import numpy as np

# local modules from "optical"
import alhazen.optical_functions
import alhazen.ScatteringMatrix

FAKE_RUN = False

DEFAULT_THICKNESS_AL = -1
DEFAULT_WL_RANGE = "200,1100"  # TODO: ask Emanuele for a proper value
DEFAULT_NP = 400  # TODO: ask Emanuele for a proper value


def convert_structure(json_structure, params):
    '''
    translate json_structure into "opt" structure: the "multilayer" object
    which is a list of "layer" objects, all defined in optical_functions.py
    (from Centurioni's optical.functions)
    '''

    logging.info(f"params:{params}")

    # get thickness of active layer from params: to be set as the thickness
    # of active layer, if any
    thickness_active_layer = float(params['model_edit_panel'].get(
        'thickness_active_layer', DEFAULT_THICKNESS_AL))
    # FIXME: thickness_active_layer dovrebbe arrivare gia` come numero e
    # invece e` una stringa!

    opt_structure = alhazen.optical_functions.multilayer()
    opt_structure.name = json_structure['name']
    for json_layer in json_structure['layers']:
        name = json_layer['name']
        active = json_layer['active']
        materials = json_layer['materials']
        # in case user set this value different from the default which is -1
        if json_layer['active'] and thickness_active_layer > 0:
            thickness = thickness_active_layer
        else:
            thickness = json_layer['thickness']
            # FIXME: thickness_active_layer in form.input must be set to the
            # actual thickness read from structure; TODO: ask Giovanni
        coherence = json_layer['coherence']
        roughness = json_layer['roughness']

        here_ = os.path.dirname(os.path.abspath(__file__))
        refractive_index_collection_path = os.path.join(
            here_, '..', '..', 'refractive_index_collection')

        kw_args = dict(
            name=name,
            file1=os.path.join(
                refractive_index_collection_path, materials[0]['fname']),
            file2=os.path.join(
                refractive_index_collection_path, materials[1]['fname']),
            file3=os.path.join(
                refractive_index_collection_path, materials[2]['fname']),
            fr1=str(materials[0]['fraction']),
            fr2=str(materials[1]['fraction']),
            fr3=str(materials[2]['fraction']),
            thickness=str(thickness/10),
            incoherent="1" if coherence == 0 else "0",
            roughness=str(roughness))

        opt_layer = alhazen.optical_functions.layer(**kw_args)

        opt_structure.add(opt_layer)

    return opt_structure


def wl_range(opt_structure, params):
    wl_min, wl_max = [float(a) for a in params['plot_edit_panel'].get(
        'wl_range', DEFAULT_WL_RANGE).split(',')]
    wl_min = max(wl_min, opt_structure.lmin)
    wl_max = min(wl_max, opt_structure.lmax)
    wl_np = int(params['plot_edit_panel'].get('wl_np', DEFAULT_NP))
    # FIXME: wl_np dovrebbe arrivare gia` come numero e invece e` una stringa!
    wl = np.linspace(wl_min, wl_max, wl_np)

    return wl


def compute_RT(json_structure, params):

    # json_ to opt_structure
    opt_structure = convert_structure(json_structure, params)

    # from Centurioni's optical.functions: for each opt_structure.layer, add
    # n,k (each with its own wl list) to the opt_structure.layer
    alhazen.optical_functions.EMA(opt_structure)

    # this find the min and max wavelenght of the whole structure and define
    # opt_structure.lmin and opt_structure.lmax
    alhazen.optical_functions.CheckWaveRange(opt_structure)

    # Domanda per Emanuele: ci sono altre chiamate necessarie?

    # wavelength list to compute R,T
    wl = wl_range(opt_structure, params)

    # get incidence angle in degrees and convert it into radians
    incidence_angle = math.pi/180 * \
        float(params['model_edit_panel']['incidence_angle'])
    # FIXME: incidence_angle dovrebbe arrivare gia` come numero e invece e`
    # una stringa!

    Ronly, Tonly = alhazen.ScatteringMatrix.ComputeRT(
        alhazen.optical_functions.PrepareList(opt_structure, wl), wl, incidence_angle)
    # WARNING: ScatteringMatrix.ComputeRT returns two numpy.ndarray with
    # containing R and T only (not the wavelength); need to be processed
    # befort return

    # prepare output in the required format
    R = []
    for l, r in zip(wl, Ronly.tolist()):
        R.append((l, r*100))

    T = []
    for l, r in zip(wl, Tonly.tolist()):
        T.append((l, r*100))

    return R, T


def get_description(_structure, params):

    message = f"params: {params}<br/>"
    message += "layers: "
    for k, v in _structure.get('structure', {}).items():
        message += f"{k} {v.get('thickness')}(µ), "

    return message
