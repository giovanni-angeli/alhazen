# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-format-interpolation

import os
import asyncio
import json
import logging
import random
import copy
import math

PARAMS_FILE = "./alhazen.params.json"

LAYER_PARAMETER_SCHEMA = {
    'name': {
        'value': "top layer",
        'description': "name",
        "type": "str",
    },
    'thickness': {
        'value': 1.3,
        'description': "thickness (Angstrom)",
        "type": "float",
        'min': 0,
        'max': 100000000, # FIXME: deve poter essere espresso in notazione scientifica 1e8
    },
    'incoherence': { #FIXME: questo dovrebbe essere reso con un thick (ed essere bool)
        'value': 0,
        'description': "0 if medium is coherent, else 1", # TODO: reverse?
        "type": "int", # FIXME: bool
        'min': 0,
        'max': 1,
    },
    'roughness': {
        'value': 0,
        'description': "roughness (Angstrom)",
        "type": "float",
        'min': 0,
        'max': 100, # TODO: chiedere Caterina limite realistico
    },
    'M1_name': {
        'value': "air",
        'description': "name of medium 1",
        "type": "str",
    },
    'M1_fraction': {
        'value': 100,
        'description': "fraction of medium 1",
        "type": "float",
        'min': 0,
        'max': 100,
    },
    'M1_opticalProps FileName': {
        'value': "",
        'description': "optical properties of medium 2",
        "type": "str",
    },
    'M2_name': {
        'value': "air",
        'description': "name of medium 2",
        "type": "str",
    },
    'M2_fraction': {
        'value': 0,
        'description': "fraction of medium 2",
        "type": "float",
        'min': 0,
        'max': 100,
    },
    'M2_opticalProps FileName': {
        'value': "",
        'description': "optical properties of medium 1",
        "type": "str",
    },
    'M3_name': {
        'value': "air",
        'description': "name of medium 3",
        "type": "str",
    },
    'M3_fraction': {
        'value': 0,
        'description': "fraction of medium 3",
        "type": "float",
        'min': 0,
        'max': 100,
    },
    'M3_opticalProps FileName': {
        'value': "",
        'description': "optical properties of medium 3",
        "type": "str",
    },
}


class Backend:

    def __init__(self):

        self.default_structure_params = {}

        self.layer_name_list = ["L1", "L2", "L3", "L4", ]

        for layer_name in self.layer_name_list:
            for k, v in LAYER_PARAMETER_SCHEMA.items():
                self.default_structure_params["{}_{}".format(layer_name, k)] = copy.deepcopy(v)

        self.params = {}
        self.params_file_path = PARAMS_FILE
        self.title = 'plot example - intensity(%) vs wavelength(nm)'

    async def run(self):

        self.reset_structure_params()
        self.load_structure_params_from_json_file()

        while True:

            await asyncio.sleep(5)

    def reset_structure_params(self):

        logging.info("")

        self.params = copy.deepcopy(self.default_structure_params)

    def dump_structure_params_to_json_file(self):

        logging.info(f"self.params_file_path:{self.params_file_path}")

        with open(self.params_file_path, 'w') as f:
            json.dump(self.params, f, indent=2)

    def load_structure_params_from_json_file(self):

        logging.debug(f"self.params_file_path:{self.params_file_path}")

        if os.path.exists(self.params_file_path):
            with open(self.params_file_path) as f:
                self.params = json.load(f)

    def load_optical_properties_from_file(self, filename):

        logging.debug(f"data_file:{filename}")

        optical_properties = []
        if os.path.exists(filename):
            with open(filename) as f:
                optical_properties = json.load(f)

        return optical_properties

    def run_model(self):

        for n in self.layer_name_list:
            fname = "{}_{}".format(n, 'M1_opticalProps FileName')
            optical_properties = self.load_optical_properties_from_file(fname)

            # ~ use loaded mproperties

        # ~ compute data to be visualized
        # ~ and format them into lines for graph
        data = []
        for i, p in enumerate(self.layer_name_list):

            k = "{}_{}".format(p, 'thickness')
            thickness = float(self.params.get(k, {}).get('value', 10))

            k = "{}_{}".format(p, 'roughness')
            roughness = float(self.params.get(k, {}).get('value', 10))

            item = {
                'line_name': f'line {p}', 
                'x_y_data':  [(j, 0.001 * thickness * j**2 + roughness * random.random()) for j in range(100)]
            }
            data.append(item)

        return data
