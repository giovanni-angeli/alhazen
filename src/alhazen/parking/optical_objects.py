# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-format-interpolation
# pylint: disable=logging-fstring-interpolation


import os
from numpy import pi, exp
from scipy.interpolate import interp1d

HERE = os.path.dirname(os.path.abspath(__file__))
MATERIAL_REFRACTIVE_INDEX_DIR = os.path.join(HERE,'..','..','refractive_index_collection')
STRUCTURE_DIR = os.path.join(HERE,'..','..','data_templates','structure_files')

class Material():
    '''
    Material is the component of an Effective Material Approximation (EMA)
        that includes up to three materials.
    Material is characterized by its Refractive Index (RI) that is stored in a file.
    Material has a name (first record of the file).
    Given a Material, the RI can be recomputed (interpolated) on a common
        wavelength (wl) grid which is the union of the real and imaginary
        part grids.
    The RI of a Material can be the resutl of a model (to be implemented).
    TODO:
    - verify if present underscoring makes sense;
    - think whether to give refractive_index_original and
      refractive_index_common in the same format and, if so, which format;
    - add read/write/edit methods;
    '''

    def __init__( self, file_name, modeled=False ):
        '''
        Initialize Material based on content of file_name
        REMARK: file_name here can be regarded as a reference to a database entry
        '''
        # FIXME: file_name and modeled should be mutually exclusive (of
        #   course, results of modeling can be saved in a file, but not in
        #   the database): how to implement it?

        self.file_name = file_name
        # QUESTION: does the following makes sense in __init__
        #           (i.e., defining a property through a call to a private method)
        # QUESTION: is it really necessary to define the property "name"?
        self.name = self._get_name()
        self.modeled = modeled

    def _get_name(self):

        with open( os.path.join(MATERIAL_REFRACTIVE_INDEX_DIR,self.file_name),
                   mode='r', encoding='utf-8' ) as f:
            # WARNING: this is for the "optical" format!
            # first record contains the material name
            name = next(f)
            f.close()

            return name

    def get_refractive_index(self):
        '''
        Refractive index as read from file. List of wavelengths for real and
        imaginary parts are different in principle; this is why it is
        returned as {'real':RIr;'imag':RIi}
        where RIr = [ ... (lambda_1, RIr_1), ...] and the same for RIi
        '''

        # FIXME: encoding can be strange for these files: use some guess tool
        with open( os.path.join(MATERIAL_REFRACTIVE_INDEX_DIR,self.file_name),
                   mode='r', encoding='utf-8' ) as f:

            # WARNING: this is for the "optical" format!

            # skip header (fixed number of lines with no particular
            # structure that can be recognised)
            #   first record contains the material name (not used here; see _get_name())
            next(f)
            #   second record contains min and max (global) wavelength, not used
            next(f)

            # read real part: wavelength, refractive index
            Nr = int(next(f)) # number of records for the real part
            RI_r = []
            for _ in range(Nr):
                wl,ri = next(f).split()
                RI_r.append( (float(wl),float(ri)) )

            # read imaginary part: wavelength, refractive index
            Ni = int(next(f)) # number of records for the imag part
            RI_i = []
            for _ in range(Ni):
                wl,ri = next(f).split()
                RI_i.append( (float(wl),float(ri)) )

            f.close()

            return { 'real': RI_r, 'imag': RI_i }

    def refractive_index(self):
        '''
        Refractive index interpolated on common grid
        WARNING: returned RI has a different form with respect to refractive_index_original
        '''

        refractive_index_original = self.get_refractive_index()

        # length of real and imaginary parts
        Nr = len(refractive_index_original['real'])
        Ni = len(refractive_index_original['imag'])

        # extract grids for real and imaginary parts
        wl_r = [ refractive_index_original['real'][i][0] for i in range(Nr) ]
        wl_i = [ refractive_index_original['imag'][i][0] for i in range(Ni) ]

        # extract values for real and imaginary parts
        RI_r = [ refractive_index_original['real'][i][1] for i in range(Nr) ]
        RI_i = [ refractive_index_original['imag'][i][1] for i in range(Ni) ]

        # build interpolation functions (use scipy.interpolate)
        # IMPORTANT: **kind must be "linear"** to avoid messing with data;
        #   if linear, any further linear interpolation will not change
        #   anything. Moreover, typical refractive index files are given on
        #   a very fine wavelenght grid so that linear interpolation is
        #   enough.
        _interp_r = interp1d( wl_r,RI_r, kind='linear', fill_value='extrapolate')
        _interp_i = interp1d( wl_i,RI_i, kind='linear', fill_value='extrapolate')

        # build common grid: union of grids for real and imaginary parts, sorted
        wl = sorted( list( set(wl_r) | set(wl_i) ) )

        # interpolate real and imaginary parts on the common grid and pack'em
        RI = [ complex(r,i) for r,i in zip(_interp_r( wl ),_interp_i( wl )) ]

        return list( zip(wl,RI) )

#    def read():
#
#    def write():
#
#    def edit():
#


class Layer():

    def __init__( self, json_layer ):
        '''
        Layer is the basic constituent of a Structure
        Layer is built from json_layer, a subset of json_structure
        '''

        self.name = json_layer['name']
        self.description = json_layer['description']
        self.active = json_layer['active']
        self.component = []
        fraction_total = 0
        for c in json_layer['components']:
            if c['material_file_name'] and c['fraction'] > 0:
                self.component.append( ( Material(c['material_file_name']), float(c['fraction']) ) )
                fraction_total += float( c['fraction'] )
        if fraction_total != 100:
            raise Exception(f"Sum of fractions is {fraction_total}%, not 100%")
        self.coherence = json_layer['coherence']
        self.thichness = json_layer['thickness']
        self.roughness = json_layer['roughness']

    def refractive_index(self):
        '''
        Compute the refractive index of the Layer based on the Effective
        Material Approximation applied to self.component
        '''

        # taken from optical.functions (almost) as it is
        def _EMA( refractive_index, fraction ):
            '''
            This is called only when len(RI) == 2 or 3 but needs the full
            length ri and fr
            '''

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

            # init working vars:
            # - fr
            fr = [0,0,0]
            fr[0:len(fraction)] = fraction
            # - ri
            ri = [ complex(0) for _ in range(3) ]
            ri[0:len(refractive_index)] = refractive_index
            # - ri^2
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

        N_comp = len(self.component)
        # if one component only: layer.refractive_index = material_refractive_index
        if N_comp == 1:
            return self.component[0][0].refractive_index()
        # else:
        # - build common grid for all of the 2 or 3 components present in
        #   the layer and get refractive index for each material
        wl_comp = []
        RI_comp = []
        fraction = []
        wl = []
        for i,c in enumerate(self.component):
            # this is just for readability: remember that c[0] is the material object
            #   while c[1] is its fraction
            material = c[0]
            fraction.append(c[1]) # fraction is needed for EMA calclations

            # How the instruction below works:
            # 0. xxx is a list of couples (tuples)
            # 1. res = zip(*xxx) un'zipped object: '*' unpack the xxx
            #    into positional arguments
            # 2. res = list( res ) # transform to a list (a list of two tuples)
            # 3. res = res[0] # take the first element which is a tuple
            # a. list( res ) # turn the tuple to a list

            # get wavelength list of i-th component ...
            RI_unzip = list(zip(*material.refractive_index()))
            wl_comp.append( list( RI_unzip[0] ) )
            # ... and add it to the commong grid
            wl.extend( wl_comp[-1] ) # is this equivalent to: wl += wl_comp ?

            # get refractive index for i-th material
            RI_comp.append( list( RI_unzip[1] ) )

        # - remove dupes and sort common grid
        wl = sorted( list( set(wl) ) )

        # - for each material, interpolate RI on the common grid
        RI = []
        for i in range(N_comp):
            # create interpolation functions
            _interp_r = interp1d( wl_comp[i],[ _.real for _ in RI_comp[i] ], \
                        kind='linear', fill_value='extrapolate' )
            _interp_i = interp1d( wl_comp[i],[ _.imag for _ in RI_comp[i] ], \
                        kind='linear', fill_value='extrapolate' )
            # interpolate on the new common grid
            RI_r = _interp_r(wl)
            RI_i = _interp_i(wl)
            # pack the result and append to RI
            RI.append( [ complex(r,i) for r,i in zip(RI_r,RI_i) ] )

        # - for each point in the wl grid compute EMA
        out = []
        for i,_wl in enumerate(wl):
            out.append( ( _wl,_EMA( [ RI[j][i] for j in range(N_comp) ],fraction ) ) )

        return out

    def read(self):
        pass

    def write(self):
        pass

    def edit(self):
        pass



class Structure():

    def __init__( self, json_structure ):

        '''
        Bisogna prevedere di poterla creare da un file?
        E anche di crearne una vuota da editare?
        '''

        self.name = json_structure['name']
        self.description = json_structure['description']
        self.layer = [ Layer(l) for l in json_structure['layers'] ]

    def _common_grid(self):
        '''
        di nuovo devo calcolare una griglia comune, questa volta a tutti i
        layers, forse sarebbe meglio usare una funzione comune a tutte le
        classi? argomento: lista di "griglie", return, gliglia unica sorted
        '''
        pass

    def compute_RT(self, params):
        # get incidence angle from params
        # PrepareList: interpolate RI
        pass

    def read(self):
        '''
        Read from file?
        Ma non ha senso se la costruisco da una json_structure!
        Dobbiamo forse spostare la lettura della json_structure qui e
        passare il nome del file alla __init__?
        '''
        pass

    def write(self):
        '''
        Write (the edited) structure to a file
        '''
        pass

    def edit(self):
        '''
        should implement functions for used in frontend for editing:
        - add a blank layer
        - add a copy of a layer
        - N-plicate selected layers (for, e.g., Bragg mirrors)
        - ...
        '''
        pass



if __name__ == '__main__':

    import json # this used only when testing (__main__)
    #import numpy as np # this used only when testing (__main__)
    import matplotlib.pyplot as plt

    STRUCTURE_FILE = 'structure-test.json'

    with open(os.path.join(STRUCTURE_DIR,STRUCTURE_FILE), encoding='utf-8') as f:
        json_structure = json.load(f)
        structure = Structure(json_structure)

        print()
        print('----')
        print( 'structure: ',vars(structure) )
        print('----')

        for i,l in enumerate(structure.layer):
            print()
            print( f"layer {i}: {vars(l)}" )
            for m,f in structure.layer[i].component:
                print( f"\tmaterial: {vars(m)}" )
                print( f"\tfraction: {f}" )

            # 1
            #print( f"\trefractive index (as it is): {l.refractive_index()}" )

            # 2
            wl,ri = zip(*l.refractive_index())
            #print( f"\trefractive index (unzip): {wl,ri}" )

            plt.plot(wl,[ _.real for _ in ri],label='n' )
            plt.plot(wl,[ _.imag for _ in ri],label='k' )
            plt.xlabel('wavelength (nm)')
            plt.ylabel('n, k')
            plt.title(f'{structure.name} - layer {i}: {l.name}')
            plt.legend()
            plt.show()

            # 3
            #print( f"\trefractive index (np.array): {np.array(l.refractive_index())}" )

        print('----')
        print()

    # TODO: add plots