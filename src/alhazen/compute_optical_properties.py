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

    # FIXME: encoding can be strange for these files: use some guess tool
    with open(os.path.join(REFRACTIVE_INDEX_DIR, fname),
              mode='r', encoding='utf-8') as fp:

        # skip header (fixed number of lines with no particular structure that can be recognised)
        #   first record contains the material name (not used here)
        next(fp)
        #   second record contains min and max (global) wavelength, not used
        next(fp)

        # read real part: wavelength, refractive index
        Nr = int(next(fp))  # number of records for the real part
        ri_r = []
        for _ in range(Nr):
            wl, ri = next(fp).split()
            ri_r.append((float(wl)/10, ri))

        # read imaginary part: wavelength, refractive index
        Ni = int(next(fp))  # number of records for the imag part
        ri_i = []
        for _ in range(Ni):
            wl, ri = next(fp).split()
            ri_i.append((float(wl)/10, ri))

        # TODO: discuss this format with Giovanni; possible alternative:
        #   a list of the union of wl_r and wl_i with 'Null' (or None)
        #   values for missing ri
        return dict(real=ri_r, imag=ri_i)


def wl_common(wl):
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
    by fname itself, build a target wl list as the union of the wl lists for
    real and imaginary parts and intepolates refractive index on this target
    grid. Returns the refractive index for the material in "standard" format
    (standard in this context).
    '''

    # get data from refractive index file
    mri = material_refractive_index_read(fname)
    wl_r = [_[0] for _ in mri['real']]
    ri_r = [_[1] for _ in mri['real']]
    wl_i = [_[0] for _ in mri['imag']]
    ri_i = [_[1] for _ in mri['imag']]

    # build interpolation functions (from scipy.interpolate)
    _interp_r = interp1d(wl_r, ri_r, kind='linear', fill_value='extrapolate')
    _interp_i = interp1d(wl_i, ri_i, kind='linear', fill_value='extrapolate')

    # build the target grid
    wl = wl_common([wl_r, wl_i])

    # iterpolate on the target grid (tolist() because output is a numpy array)
    ri_r = _interp_r(wl).tolist()
    ri_i = _interp_i(wl).tolist()

    return [(wl[i], complex(ri_r[i], ri_i[i])) for i in range(len(wl))]


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

    # check EMA consistency
    fraction_total = 0
    for i,c in enumerate(json_layer['components']):
        if c['fraction'] == 0:
            raise Exception(f"no EMA components with zero fraction allowed: {c}")
        fraction_total += c['fraction']
    if fraction_total != 100:
        raise Exception(f"EMA components total fraction exceeds 100%: {json_layer['components']}")

    Nc = len(json_layer['components'])
    if Nc == 1:
        return material_refractive_index(json_layer['components'][0]['material_file_name'])
    # compute refractive index for EMA:
    # - extract info for each component
    fraction = []
    _wl = []
    _ri = []
    for c in json_layer['components']:
        fraction.append(c['fraction'])
        mri = material_refractive_index(c['material_file_name'])
        _wl.append([_[0] for _ in mri])
        _ri.append([_[1] for _ in mri])

    # - create target grid
    wl = wl_common(_wl)

    # - for each material, interpolate _RI on the common grid
    ri = []
    for i in range(Nc):
        # build interpolation functions
        _interp_r = interp1d(_wl[i], [_.real for _ in _ri[i]],
                             kind='linear', fill_value='extrapolate')
        _interp_i = interp1d(_wl[i], [_.imag for _ in _ri[i]],
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

    return list(zip(wl, ema))


def wl_grid(wl_list, params):
    '''
    Builds the target wl grid for output.
    '''

    # TODO: implement 'auto' option (ignore user provided min and max)

    # user defined min and max wl
    u_wl_min, u_wl_max = [float(a) for a in params['plot_edit_panel'].get(
        'wl_range', DEFAULT_WL_RANGE).split(',')]

    # find min and max wl fro the structure
    s_wl_min = -np.inf
    s_wl_max = +np.inf
    for _wl in wl_list:
        s_wl_min = max(s_wl_min, min(_wl))
        s_wl_max = min(s_wl_max, max(_wl))

    # define min and max of wl range and create a linear grid
    wl_min = max(u_wl_min, s_wl_min)
    wl_max = min(u_wl_max, s_wl_max)
    wl_np = int(params['plot_edit_panel'].get('wl_np', DEFAULT_NP))
    wl = np.linspace(wl_min, wl_max, wl_np)

    return wl


def prepare_ScatteringMatrix_input(json_structure, params):
    '''
    This is equivalent to optical.functions.PrepareList
    '''

    _wl = []
    _ri = []
    for layer in json_structure['layers']:
        lri = layer_refractive_index(layer)
        # FIXME: giovanni dice che e` meglio list comprehension
        _wl.append(list(list(zip(*lri))[0]))
        _ri.append(list(list(zip(*lri))[1]))

    # prepare target grid
    wl = wl_grid(_wl, params)

    SM_structure = []
    for i, layer in enumerate(json_structure['layers']):

        # interpolate and arrange ri as complex
        # - build interpolate functions
        _interp_r = interp1d(_wl[i], [_.real for _ in _ri[i]],
                             kind='linear', fill_value='extrapolate')
        _interp_i = interp1d(_wl[i], [_.imag for _ in _ri[i]],
                             kind='linear', fill_value='extrapolate')

        # interpolate and arrange ri as complex
        ri_r = _interp_r(wl).tolist()
        ri_i = _interp_i(wl).tolist()
        ri = [complex(r, i) for r, i in zip(ri_r, ri_i)]

        # convert coherence (bool) to incoherent (int)
        incoherent = 1 if layer['coherence'] == 0 else 0

        SM_structure.append([float(layer['thickness'])/10, ri,
                             incoherent, float(layer['roughness'])])

    return wl, SM_structure


def compute_RT(json_structure, params):

    # prepare structure data
    wl, SM_structure = prepare_ScatteringMatrix_input(json_structure, params)

    # get incidence angle in degrees and convert it into radians
    incidence_angle = np.pi/180 * \
        float(params['model_edit_panel']['incidence_angle'])

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
