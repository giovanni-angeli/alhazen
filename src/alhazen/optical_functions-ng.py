# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-format-interpolation
# pylint: disable=logging-fstring-interpolation

import os

from numpy import pi, exp
from scipy.interpolate import interp1d

HERE = os.path.dirname(os.path.abspath(__file__))
MATERIAL_REFRACTIVE_INDEX_DIR = os.path.join(
    HERE, '..', '..', 'refractive_index_collection')
STRUCTURE_DIR = os.path.join(
    HERE, '..', '..', 'data_templates', 'structure_files')


def material_refractive_index_read(fname):

    # FIXME: encoding can be strange for these files: use some guess tool
    with open(os.path.join(MATERIAL_REFRACTIVE_INDEX_DIR, fname),
              mode='r', encoding='utf-8') as fp:

        # WARNING: this is for the "optical" format!

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
            wl_r.append(float(wl))
            ri_r.append(float(ri))

        # read imaginary part: wavelength, refractive index
        Ni = int(next(fp))  # number of records for the imag part
        wl_i = []
        ri_i = []
        for _ in range(Ni):
            wl, ri = next(fp).split()
            wl_i.append(float(wl))
            ri_i.append(float(ri))

        return dict(real=dict(wl=wl_r, ri=ri_r), imag=dict(wl=wl_i, ri=ri_i))

def wl_grid(wl):

    wl_set = set()
    for _wl in wl:
        wl_set = wl_set | set(_wl)
    return sorted(list(wl_set))

def material_refractive_index(fname):

    # read data from refractive index file
    RI = material_refractive_index_read(fname)

    # build interpolation functions (from scipy.interpolate)
    _interp_r = interp1d(RI['real']['wl'], RI['real']['ri'],
                         kind='linear', fill_value='extrapolate')
    _interp_i = interp1d(RI['imag']['wl'], RI['imag']['ri'],
                         kind='linear', fill_value='extrapolate')

    # build the target grid
    wl = wl_grid([RI['real']['wl'], RI['imag']['wl']])

    # iterpolate over the target grid
    RI_r = _interp_r(wl).tolist()
    RI_i = _interp_i(wl).tolist()

    # build complex refractive index
    #RI = [complex(r, i) for r, i in zip(_interp_r(wl), _interp_i(wl))]

    #return dict(wl=wl, RI=RI)
    return dict(wl=wl, ri=dict(real=RI_r, imag=RI_i))

def compute_EMA( refractive_index, fraction ):

    # taken from optical.functions as it is
    def _root3(a,b,c,d):
        #finds roots of eq ax^3+bx^2+cx+d=0
        a,b,c=b/a,c/a,d/a
        p=(-a**2)/3+b
        q=(2*a**3)/27-a*b/3+c
        u1=(-q/2+((q**2)/4+(p**3)/27)**(0.5))**(1.0/3)
        u,x=[],[]
        u.append(u1)#there are 3 roots for u
        u.append(u1*exp(2*pi/3*1j))
        u.append(u1*exp(4*pi/3*1j))
        for i in range(3):
            x.append(u[i]-p/(3*u[i])-a/3)
        return x

    # initialize working vars:
    if len(fraction) != len(refractive_index):
        raise Exception("Error in EMA number of components definition")
    # fill the missing third component (if necessary)
    # - fr
    fr = [0,0,0]
    fr[0:len(fraction)] = fraction
    # - ri
    ri = [ complex(0) for _ in range(3) ]
    ri[0:len(refractive_index)] = refractive_index
    # compute auxiliaty var ri2 = ri**2
    ri2 = [ ri[i]**2 for i in range(len(ri)) ]

    nguess=fr[0]*ri[0]+fr[1]*ri[1]+fr[2]*ri[2]
    a = -4
    b = fr[0]*( 4*ri2[0] -2*(ri2[1]+ri2[2] )) \
       +fr[1]*( 4*ri2[1] -2*(ri2[0]+ri2[2] )) \
       +fr[2]*( 4*ri2[2] -2*(ri2[0]+ri2[1] ))
    c = fr[0]*( 2*ri2[0]*(ri2[1]+ri2[2]) -ri2[1]*ri2[2] ) \
       +fr[1]*( 2*ri2[1]*(ri2[0]+ri2[2]) -ri2[0]*ri2[2] ) \
       +fr[2]*( 2*ri2[2]*(ri2[0]+ri2[1]) -ri2[0]*ri2[1] )
    d = (fr[0]+fr[1]+fr[2])*(ri2[0]*ri2[1]*ri2[2])
    e = _root3(a,b,c,d)
    pn = [e[0]**(0.5),e[1]**(0.5),e[2]**(0.5)]
    distance = [abs(pn[0]-nguess), abs(pn[1]-nguess), abs(pn[2]-nguess)]
    return pn[distance.index(min(distance))]

def layer_refractive_index(json_layer):

    Nc = len(json_layer['components'])
    if  Nc == 1:
        return material_refractive_index(json_layer['components'][0]['material_file_name'])
    # compute refractive index for EMA:
    # - extract info for each component
    fraction = []
    _wl = []
    _ri = []
    for c in json_layer['components']:
        fraction.append(c['fraction'])
        _wl.append(material_refractive_index(c['material_file_name'])['wl'])
        _ri.append(material_refractive_index(c['material_file_name'])['ri'])

    # - create target grid
    wl = wl_grid( _wl )

    # - for each material, interpolate _RI on the common grid
    RI = []
    for i in range(Nc):
        # build interpolation functions
        _interp_r = interp1d(_wl[i], _ri[i]['real'],
                             kind='linear', fill_value='extrapolate')
        _interp_i = interp1d(_wl[i], _ri[i]['imag'],
                             kind='linear', fill_value='extrapolate')
        # interpolate on the new common grid
        ri_r = _interp_r(wl)
        ri_i = _interp_i(wl)
        # pack the result and append to RI
        RI.append( [ complex(r,i) for r,i in zip(ri_r,ri_i) ] )

    # - for each point in the wl grid compute EMA
    ema = []
    for i,_wl in enumerate(wl):
        ema.append( ( compute_EMA( [ RI[j][i] for j in range(Nc) ],fraction ) ) )

    return dict( wl=wl, ri=dict(real=[_.real for _ in ema], imag=[_.imag for _ in ema]) )


if __name__ == '__main__':

    import json
    import matplotlib.pyplot as plt

    STRUCTURE_FILE = 'structure-test.json'

    with open(os.path.join(STRUCTURE_DIR, STRUCTURE_FILE), encoding='utf-8') as f:
        json_structure = json.load(f)

    for i,layer in enumerate(json_structure['layers']):

        #print(f"layer: {layer['name']}")

        RI = layer_refractive_index(layer)
        #print(f"- refractive index: {RI}")

        plt.plot(RI['wl'],RI['ri']['real'],label='n' )
        plt.plot(RI['wl'],RI['ri']['imag'],label='k' )
        plt.xlabel('wavelength (nm)')
        plt.ylabel('n, k')
        plt.title(f"{json_structure['name']} - layer {i}: {layer['name']}")
        plt.legend()
        plt.show()

