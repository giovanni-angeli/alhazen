# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-format-interpolation
# pylint: disable=logging-fstring-interpolation


import os

# this is only for main() (test function)
import json

from scipy.interpolate import interp1d


# This is the path for the material database. Does it goes here?
MATERIAL_REFRACTIVE_INDEX_DIR = '.'

class Material():
    '''
    Material is the component of an Effective Material Approximation (EMA)
    that includes upt to three materials.
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
        self.name = self._get_name()
        # QUESTION: does the following makes sense in __init__
        #           (i.e., defining a property through a call to a private method)
        self.refractive_index_original = self._get_refractive_index()
        self.modeled = modeled

    def _get_name(self):

        with open( os.path.join(MATERIAL_REFRACTIVE_INDEX_DIR,self.file_name),
                   mode='r', encoding='utf-8' ) as f:
            # WARNING: this is for the "optical" format!
            # first record contains the material name
            name = next(f)
            f.close()

            return name

    def _get_refractive_index(self):
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

    def refractive_index_common(self):
        '''
        Refractive index interpolated on common grid
        WARNING: returned RI has a different form with respect to refractive_index_original
        '''

        # length of real and imaginary parts
        Nr = len(self.refractive_index_original['real'])
        Ni = len(self.refractive_index_original['imag'])

        # extract grids for real and imaginary parts
        _wl_r = [ self.refractive_index_original['real'][i][0] for i in range(Nr) ]
        _wl_i = [ self.refractive_index_original['imag'][i][0] for i in range(Ni) ]

        # extract values for real and imaginary parts
        _RI_r = [ self.refractive_index_original['real'][i][1] for i in range(Nr) ]
        _RI_i = [ self.refractive_index_original['imag'][i][1] for i in range(Ni) ]

        # build interpolation functions (use scipy)
        # IMPORTANT: must be "linear" to avoid messing with data; if linear,
        #   any further linear interpolation will not change anything.
        #   Moreover, typical refractive index files are given on a very
        #   fine wavelenght grid so that linear interpolation is enough.
        _interp_r = interp1d( _wl_r,_RI_r, kind='linear', fill_value='extrapolate')
        _interp_i = interp1d( _wl_i,_RI_i, kind='linear', fill_value='extrapolate')

        # build common grid: union of grids for real and imaginary parts, sorted
        wl_common = sorted( list( set(_wl_r) | set(_wl_i) ) )

        # interpolate real and imaginary parts on the common grid
        RI_r = _interp_r( wl_common )
        RI_i = _interp_i( wl_common )
        RI = [ complex( RI_r[i], RI_i[i] ) for i in range( len(wl_common) ) ]

        return list( zip(wl_common,RI) )

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

        # if one component only: layer.refractive_index = material_refractive_index
        if len(self.component) == 1:
            return self.component[0].refractive_index_common
        # - build common grid for all the 2 or 3 components present in the
        #   layer and get refractive index for each material
        _wl = []
        _RI = []
        fraction = []
        wl = []
        for i,c in enumerate(self.component):
            material = c[0]
            # the above is just for readability: remember that c[0] is the material object
            #   while c[1] is its fraction
            fraction.append(c[1]) # fraction is needed for EMA calclations

            # How the instruction below works:
            # xxx is a list of couples
            # 1. res = zip(*xxx) # 'un'zipped object
            # 2. res = list( res ) # transform to a list (a list of two tuples)
            # 3. res = res[0] # take the first element which is a tuple
            # a. list( res ) # turn the tuple to a list

            # get wavelength list of i-th component ...
            _wl.append( list( list(zip(*material.refractive_index))[0]) )
            # ... and add it to the commong grid
            wl.extend( _wl ) # is this equivalent to: wl += _wl ?

            # get refractive index for i-th material
            _RI.append( list( list(zip(*material.refractive_index))[1] ) )

        # - remove dupes and sort common grid
        wl = sorted( list( set(_wl) ) )

        # - for each material, interpolate RI on the common grid
        RI = []
        for i in enumerate(_wl):
            # create interpolation functions
            _interp_r = interp1d( _wl[i],_RI[i].real, kind='linear', fill_value='extrapolate')
            _interp_i = interp1d( _wl[i],_RI[i].imag, kind='linear', fill_value='extrapolate')
            # interpolate on the new common grid
            RI_r = _interp_r(wl)
            RI_i = _interp_i(wl)
            # pack the result and append to RI
            RI.append( [ complex(r,i) for r,i in zip(RI_r,RI_i) ] )

        # - for each point in the wl grid compute EMA
        for i in enumerate(wl):
            self._EMA( RI[:][i],fraction )
            # TODO: ogni risultato va messo in coppia con wl e appeso alla lista di output

        return False

    def _EMA( self,RI,fraction ):

        ri = [0,0,0]
        ri[0:len(RI)] = RI

        fr = [0,0,0]
        fr[0:len(fraction)] = fraction

        ri2 = [ ri[i]**2 for i in enumerate(ri) ]

        nguess=fr[0]*ri[0]+fr[1]*ri[1]+fr[2]*ri[2]
        a = -4
        b = fr[0]*(4*ri2[0]-2*(ri2[1]+ri2[2])) \
           +fr[1]*(4*ri2[1]-2*(ri2[0]+ri2[2])) \
           +fr[2]*(4*ri2[2]-2*(ri2[0]+ri2[1]))
        c = fr[0]*(2*ri2[0]*(ri2[1]+ri2[2])-ri2[1]*ri2[2]) \
           +fr[1]*(2*ri2[1]*(ri2[0]+ri2[2])-ri2[0]*ri2[2]) \
           +fr[2]*(2*ri2[2]*(ri2[0]+ri2[1])-ri2[0]*ri2[1])
        d = (fr[0]+fr[1]+fr[2])*(ri2[0]*ri2[1]*ri2[2])
        e = self.root3(a,b,c,d)
        pn = [e[0]**(0.5),e[1]**(0.5),e[2]**(0.5)]
        distance = [abs(pn[0]-nguess), abs(pn[1]-nguess), abs(pn[2]-nguess)]
        return pn[distance.index(min(distance))]

    def root3(self,a,b,c,d):
        # TODO: implement root3
        res = a*b*c*d
        return [res,res,res]

#    def read():
#
#    def write():
#
#    def edit():
#


class Structure():

    def __init__( self, json_structure ):

        self.name = json_structure['name']
        self.description = json_structure['description']
        self.layer = [ Layer(l) for l in json_structure['layers'] ]

#    def read():
#
#    def write():
#
#    def edit():
#


def main():

    with open('structure-template++.json', encoding='utf-8') as f:
        json_structure = json.load(f)
        structure = Structure(json_structure)

    print( 'structure: ',vars(structure.layer[0]) )
    print()

    print( 'first layer: ',vars(structure.layer[0]) )
    print()

#    print( 'first material of first layer: ',vars(structure.layer[0].component[0]) )
#    print( 'first material of first layer: ',
#           vars(structure.layer[0].component[0]['material_file_name']) )
#    print()
    print( 'first material of first layer: ',vars(structure.layer[0].component[0][0]) )
    print( 'first fraction of first material of first layer: ',structure.layer[0].component[0][1] )
    print( structure.layer[0].component[0][0].refractive_index_original )
    print( 'RI common: ',structure.layer[0].component[0][0].refractive_index_common() )

#    material = structure.layer[0].component[0][0]
#    fraction = structure.layer[0].component[0][1]
#    print( material.name, fraction )

#    structure.layer[0].component[0][0].modeled = True
#    material = structure.layer[0].component[0][0]
#    print( material.modeled )

if __name__ == '__main__':
    main()
