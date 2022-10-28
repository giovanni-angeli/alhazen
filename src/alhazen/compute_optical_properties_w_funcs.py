# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-format-interpolation
# pylint: disable=logging-fstring-interpolation

import os

import numpy as np
from scipy.interpolate import interp1d

import alhazen.ScatteringMatrix

# paths
HERE = os.path.dirname(os.path.abspath(__file__))
REFRACTIVE_INDEX_DIR = os.path.join(
    HERE, '..', '..', 'refractive_index_collection')
STRUCTURE_DIR = os.path.join(
    HERE, '..', '..', 'data_templates', 'structure_files')

# default values
DEFAULT_THICKNESS_AL = -1
DEFAULT_WL_RANGE = "200,1100"  # TODO: ask Emanuele for a proper value
DEFAULT_NP = 400  # TODO: ask Emanuele for a proper value


def material_refractive_index_read(fname):
    '''
    Reads from fname the refractive index of the material "addressed" by
    fname itself. Returns the content of the file as dictionary with
    separated 'real' and 'imaginary' parts (see return statement)
    '''

    #print(f'debug:material_refractive_index_read:fname: {fname}')
    # FIXME: encoding can be strange for these files: use some guess tool
    with open(os.path.join(REFRACTIVE_INDEX_DIR, fname),
              mode='r', encoding='utf-8') as fp:

        # WARNING: this is for files in the "optical" format!

        # skip header (fixed number of lines with no particular structure that can be recognised)
        #   first record contains the material name (not used here)
        next(fp)
        #   second record contains min and max (global) wavelength, not used
        next(fp)

        # read real part: wavelength, refractive index
        Nr = int(next(fp))  # number of records for the real part
        wl_r = []
        ri_r = []
        for _ in range(Nr):
            wl, ri = next(fp).split()
            wl_r.append(float(wl)/10)
            ri_r.append(float(ri))

        # read imaginary part: wavelength, refractive index
        Ni = int(next(fp))  # number of records for the imag part
        wl_i = []
        ri_i = []
        for _ in range(Ni):
            wl, ri = next(fp).split()
            wl_i.append(float(wl)/10)
            ri_i.append(float(ri))

        # TODO: discuss this format with Giovanni
        return dict(real=dict(wl=wl_r, ri=ri_r), imag=dict(wl=wl_i, ri=ri_i))


def wl_grid(wl):
    '''
    Given a list of lists (wavelengths in this context), returns a list
    containing the sorted union of the input lists
    '''

    wl_set = set()
    for _wl in wl:
        wl_set = wl_set | set(_wl)
    return sorted(list(wl_set))


def material_refractive_index(fname):
    '''
    Given fname containing the refractive index of the material "addressed"
    by fname itself, build a target wl list based on the wl lists for
    real and imaginary parts and intepolates refractive index on this target
    grid. Returns the refractive index for the material in "standard" format
    (standard in this context).
    '''

    # get data from refractive index file
    mri = material_refractive_index_read(fname)

    # build interpolation functions (from scipy.interpolate)
    _interp_r = interp1d(mri['real']['wl'], mri['real']['ri'],
                         kind='linear', fill_value='extrapolate')
    _interp_i = interp1d(mri['imag']['wl'], mri['imag']['ri'],
                         kind='linear', fill_value='extrapolate')

    # build the target grid
    wl = wl_grid([mri['real']['wl'], mri['imag']['wl']])

    # iterpolate on the target grid
    RI_r = _interp_r(wl).tolist()
    RI_i = _interp_i(wl).tolist()

    return dict(wl=wl, ri=dict(real=RI_r, imag=RI_i))


def compute_EMA(refractive_index, fraction):
    '''
    Given a list of refractive indices in "standard" format, returns the refractive index of the
    layer computed using the Effective Material Approximation (EMA)
    [TODO: add reference]
    '''

    # taken from optical.functions as it is
    def _root3(a, b, c, d):
        '''
        Finds the roots of equation ax^3+bx^2+cx+d=0
        '''
        a, b, c = b/a, c/a, d/a
        p = (-a**2)/3+b
        q = (2*a**3)/27-a*b/3+c
        u1 = (-q/2+((q**2)/4+(p**3)/27)**(0.5))**(1.0/3)
        u, x = [], []
        u.append(u1)  # there are 3 roots for u
        u.append(u1*np.exp(2*np.pi/3*1j))
        u.append(u1*np.exp(4*np.pi/3*1j))
        for i in range(3):
            x.append(u[i]-p/(3*u[i])-a/3)
        return x

    # initialize working vars:
    # - verify consistency of input
    if len(fraction) != len(refractive_index):
        raise Exception("Error in EMA number of components definition")
    # - fill the missing third component (if necessary)
    #   - fr
    fr = [0, 0, 0]
    fr[0:len(fraction)] = fraction
    #   - ri
    ri = [complex(0) for _ in range(3)]
    ri[0:len(refractive_index)] = refractive_index
    # - compute auxiliaty var ri2 = ri**2
    ri2 = [ri[i]**2 for i in range(len(ri))]

    nguess = fr[0]*ri[0]+fr[1]*ri[1]+fr[2]*ri[2]
    a = -4
    b = fr[0]*(4*ri2[0] - 2*(ri2[1]+ri2[2])) \
        + fr[1]*(4*ri2[1] - 2*(ri2[0]+ri2[2])) \
        + fr[2]*(4*ri2[2] - 2*(ri2[0]+ri2[1]))
    c = fr[0]*(2*ri2[0]*(ri2[1]+ri2[2]) - ri2[1]*ri2[2]) \
        + fr[1]*(2*ri2[1]*(ri2[0]+ri2[2]) - ri2[0]*ri2[2]) \
        + fr[2]*(2*ri2[2]*(ri2[0]+ri2[1]) - ri2[0]*ri2[1])
    d = (fr[0]+fr[1]+fr[2])*(ri2[0]*ri2[1]*ri2[2])
    e = _root3(a, b, c, d)
    pn = [e[0]**(0.5), e[1]**(0.5), e[2]**(0.5)]
    distance = [abs(pn[0]-nguess), abs(pn[1]-nguess), abs(pn[2]-nguess)]

    return pn[distance.index(min(distance))]

def layer_refractive_index(json_layer):
    '''
    Given a layer in json format, computes the refractive index of the layer
    (either the RI of the material if only one component, or the EMA of the two or
    three materials composing the layer) on a wl list, union of the wl lists
    of the materials composing the layer.
    '''

    Nc = len(json_layer['components'])
    if Nc == 1:
        qaz=material_refractive_index(json_layer['components'][0]['material_file_name'])
        print(f'qaz!: {qaz}')
        return material_refractive_index(json_layer['components'][0]['material_file_name'])
    # compute refractive index for EMA:
    # - extract info for each component
    fraction = []
    _wl = []
    _ri = []
    for c in json_layer['components']:
        fraction.append(c['fraction'])
        mri = material_refractive_index(c['material_file_name'])
        _wl.append(mri['wl'])
        _ri.append(mri['ri'])

    # - create target grid
    wl = wl_grid(_wl)

    # - for each material, interpolate _RI on the common grid
    ri = []
    for i in range(Nc):
        # build interpolation functions
        _interp_r = interp1d(_wl[i], _ri[i]['real'],
                             kind='linear', fill_value='extrapolate')
        _interp_i = interp1d(_wl[i], _ri[i]['imag'],
                             kind='linear', fill_value='extrapolate')
        # interpolate on the new common grid
        ri_r = _interp_r(wl).tolist()
        ri_i = _interp_i(wl).tolist()
        # pack the result and append to RI
        ri.append([complex(r, i) for r, i in zip(ri_r, ri_i)])

    # - for each point in the wl grid compute EMA
    ema = []
    for i, _wl in enumerate(wl):
        ema.append((compute_EMA([ri[j][i] for j in range(Nc)], fraction)))

    return dict(wl=wl, ri=dict(real=[_.real for _ in ema], imag=[_.imag for _ in ema]))


def prepare_ScatteringMatrix_input(json_structure, RI, wl):
    '''
    This SHOULD BE (but so far is not; FIXME!) (more or less) equivalent to optical.functions.PrepareList
    '''

    SM_structure = []
    ri = []
    for i,layer in enumerate(json_structure['layers']):

        # interpolate and arrange ri as complex
        # - build interpolate functions
        _interp_r = interp1d(RI[i]['wl'], RI[i]['ri']['real'],
                             kind='linear', fill_value='extrapolate')
        _interp_i = interp1d(RI[i]['wl'], RI[i]['ri']['imag'],
                             kind='linear', fill_value='extrapolate')

        # interpolate and arrange ri as complex
        ri_r = _interp_r(wl).tolist()
        ri_i = _interp_i(wl).tolist()
        ri.append([complex(r, i) for r, i in zip(ri_r, ri_i)])
        #print(f'debug: prepare_ScatteringMatrix_input:len(ri): {len(ri)}')

        # convert coherence (bool) to incoherent (int)
        incoherent = 1 if layer['coherence'] == 0 else 0

        SM_structure.append([float(layer['thickness']), ri,
                          incoherent, float(layer['roughness'])])

    return SM_structure

def wl_range(RI, params):
    '''
    Builds the target wl grid for output.
    '''

    # TODO: implement 'auto' option (ignore user provided min and max)

    # user defined min and max wl
    u_wl_min, u_wl_max = [float(a) for a in params['plot_edit_panel'].get(
        'wl_range', DEFAULT_WL_RANGE).split(',')]

    # find global min and max wl of the structure
    s_wl_min = max([min(ri['wl']) for ri in RI ])
    s_wl_max = min([max(ri['wl']) for ri in RI ])
    #print(f'debug:wl_range:structure min and max: {s_wl_min, s_wl_max}')
    #print(f'debug:wl_range:user min and max: {u_wl_min, u_wl_max}')

    # define min and max of wl range and create a linear grid
    wl_min = max(u_wl_min, s_wl_min)
    wl_max = min(u_wl_max, s_wl_max)
    wl_np = int(params['plot_edit_panel'].get('wl_np', DEFAULT_NP))
    wl = np.linspace(wl_min, wl_max, wl_np)

    return wl

def compute_RT(json_structure, params):

    RI = []
    for layer in json_structure['layers']:
        RI.append(layer_refractive_index(layer))
    # FIXME: RI e` sbagliato: ogni elemento e` una lista!!!
    #print(f'debug:')

    # prepare target grid
    wl = wl_range( RI, params )
    #print(f'debug:prepare_ScatteringMatrix_input:input:wl: {wl}')

    # prepare structure data
    SM_structure = prepare_ScatteringMatrix_input(json_structure, RI, wl)

    # get incidence angle in degrees and convert it into radians
    incidence_angle = np.pi/180 * \
        float(params['model_edit_panel']['incidence_angle'])

    # FIXME: quello che entra qui e` sbagliato
    for i,zaq in enumerate(SM_structure):
        print(f'debug:compute_RT:PrepareList: layer[{i}]:\n- thickness {zaq[0]}\n- RI: {zaq[1][0], zaq[1][-1]}\n- incoherent: {zaq[2]}\n- roughness: {zaq[3]}')

    Ronly, Tonly = alhazen.ScatteringMatrix.ComputeRT(
        SM_structure, wl, incidence_angle)
    # WARNING: ScatteringMatrix.ComputeRT returns two numpy.ndarray
    # containing R and T only (not the wavelength); need to be processed
    # before return

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

if __name__ == '__main__':

    import json
    import matplotlib.pyplot as plt

    import ScatteringMatrix

    STRUCTURE_FILE = 'structure-test.json'

    params={'plot_edit_panel': {'wl_range': '200, 1100', 'wl_np': '400', 'show_R': 'on', 'show_T': 'on'},
            'model_edit_panel': {'thickness_active_layer': '-1', 'incidence_angle': '0'} }

    with open(os.path.join(STRUCTURE_DIR, STRUCTURE_FILE), encoding='utf-8') as f:
        json_structure = json.load(f)

#    # add "properties" to structure
#    json_structure = dict_extend( json_structure, {'wl_min': None, 'wl_max': None} )

    RI = []
    for i, layer in enumerate(json_structure['layers']):

        #print(f"layer: {layer['name']}")

        RI.append(layer_refractive_index(layer))
        #print(f"- refractive index: {RI[i]}")

        # TODO: test interpolation by plotting also original values from file

        plt.plot(RI[i]['wl'], RI[i]['ri']['real'], label='n')
        plt.plot(RI[i]['wl'], RI[i]['ri']['imag'], label='k')
        plt.xlabel('wavelength (nm)')
        plt.ylabel('n, k')
        plt.title(f"{json_structure['name']} - layer {i}: {layer['name']}")
        plt.legend()
        plt.show()

    R,T = compute_RT(json_structure, RI, params)

