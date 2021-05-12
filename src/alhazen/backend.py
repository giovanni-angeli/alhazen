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
        'value': 0,
        'description': "thickness (nm)",
        "type": "float",
        'min': 0,
        'max': 10,
    },
    'coherence': {
        'value': 0,
        'description': "1 if medium is coherent, else 0",
        "type": "int",
        'min': 0,
        'max': 1,
    },
    'roughness': {
        'value': 0,
        'description': "roughness ()",
        "type": "float",
        'min': 0,
        'max': 10,
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
        'description': "optical properties of medium 1",
        "type": "str",
    },
}


class Backend:

    def __init__(self):

        self.default_params = {}

        self.layer_name_list = ["L1", "L2", "L3", ]

        for layer_name in self.layer_name_list:
            self.default_params.update(
                {"{}_{}".format(layer_name, k): v for k, v in LAYER_PARAMETER_SCHEMA.items()})

        self.params = {}
        self.params_file_path = PARAMS_FILE
        self.title = 'plot example - intensity(%) vs wavelength(nm)'

    async def run(self):

        self.reset_params()
        self.load_params_from_json_file()

        while True:

            await asyncio.sleep(5)

    def reset_params(self):

        logging.info("")

        self.params = copy.deepcopy(self.default_params)

    def dump_params_to_json_file(self):

        logging.info(f"self.params_file_path:{self.params_file_path}")

        with open(self.params_file_path, 'w') as f:
            json.dump(self.params, f, indent=2)

    def load_params_from_json_file(self):

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

        return data
