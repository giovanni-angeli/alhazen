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

class Backend:

    default_params = {
# layer 1
        'layer1_name': {
            'value': "top layer",
            'description': "name of layer 1",
            "type": "str",
        },
        'layer1_thickness': {
            'value': 0,
            'description': "thickness of layer 1",
            "type": "float",
            'min': 0,
            'max': 10,
        },
        'layer1_coherence': {
            'value': False,
            'description': "coherence of layer 1",
            "type": "bool",
        },
        'layer1_roughness': {
            'value': 0,
            'description': "roughness of layer 1",
            "type": "float",
            'min': 0,
            'max': 10,
        },
        'layer1_medium1_name': {
            'value': "air",
            'description': "name of medium 1 of layer 1",
            "type": "str",
        },
        'layer1_medium1_fraction': {
            'value': 100,
            'description': "fraction of medium 1 of layer 1",
            "type": "float",
            'min': 0,
            'max': 100,
        },
        'layer1_medium1_opticalPropertiesFileName': {
            'value': "",
            'description': "optical properties of medium 1 of layer 1",
            "type": "str",
        },

# layer 2
        'layer2_name': {
            'value': "top layer",
            'description': "name of layer 2",
            "type": "str",
        },
        'layer2_thickness': {
            'value': 0,
            'description': "thickness of layer 2",
            "type": "float",
            'min': 0,
            'max': 10,
        },
        'layer2_coherence': {
            'value': False,
            'description': "coherence of layer 2",
            "type": "bool",
        },
        'layer2_roughness': {
            'value': 0,
            'description': "roughness of layer 2",
            "type": "float",
            'min': 0,
            'max': 10,
        },
        'layer2_medium1_name': {
            'value': "air",
            'description': "name of medium 1 of layer 2",
            "type": "str",
        },
        'layer2_medium1_fraction': {
            'value': 100,
            'description': "fraction of medium 1 of layer 2",
            "type": "float",
            'min': 0,
            'max': 100,
        },
        'layer2_medium1_opticalPropertiesFileName': {
            'value': "",
            'description': "optical properties of medium 1 of layer 2",
            "type": "str",
        },

# layer 3
        'layer3_name': {
            'value': "top layer",
            'description': "name of layer 3",
            "type": "str",
        },
        'layer3_thickness': {
            'value': 0,
            'description': "thickness of layer 3",
            "type": "float",
            'min': 0,
            'max': 10,
        },
        'layer3_coherence': {
            'value': False,
            'description': "coherence of layer 3",
            "type": "bool",
        },
        'layer3_roughness': {
            'value': 0,
            'description': "roughness of layer 3",
            "type": "float",
            'min': 0,
            'max': 10,
        },
        'layer3_medium1_name': {
            'value': "air",
            'description': "name of medium 1 of layer 3",
            "type": "str",
        },
        'layer3_medium1_fraction': {
            'value': 100,
            'description': "fraction of medium 1 of layer 3",
            "type": "float",
            'min': 0,
            'max': 100,
        },
        'layer3_medium1_opticalPropertiesFileName': {
            'value': "",
            'description': "optical properties of medium 1 of layer 3",
            "type": "str",
        },

# layer 4
        'layer4_name': {
            'value': "top layer",
            'description': "name of layer 4",
            "type": "str",
        },
        'layer4_thickness': {
            'value': 0,
            'description': "thickness of layer 4",
            "type": "float",
            'min': 0,
            'max': 10,
        },
        'layer4_coherence': {
            'value': False,
            'description': "coherence of layer 4",
            "type": "bool",
        },
        'layer4_roughness': {
            'value': 0,
            'description': "roughness of layer 4",
            "type": "float",
            'min': 0,
            'max': 10,
        },
        'layer4_medium1_name': {
            'value': "air",
            'description': "name of medium 1 of layer 4",
            "type": "str",
        },
        'layer4_medium1_fraction': {
            'value': 100,
            'description': "fraction of medium 1 of layer 4",
            "type": "float",
            'min': 0,
            'max': 100,
        },
        'layer4_medium1_opticalPropertiesFileName': {
            'value': "",
            'description': "optical properties of medium 1 of layer 4",
            "type": "str",
        },
    }

    params = {}
    params_file_path = PARAMS_FILE
    title = 'plot example - intensity(%) vs wavelength(nm)'

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

    def load_data_from_json_file(self):

        data_file = self.params['data_file']['value']

        logging.debug(f"data_file:{data_file}")

        samples = []
        if os.path.exists(data_file):
            with open(data_file) as f:
                samples = json.load(f)

        return samples

    def run_model(self):

        samples = self.load_data_from_json_file()

        # ~ TODO: compute data from samples

        noise_rate = float(self.params.get('noise_rate', {}).get('value', 0.1))

        data = samples
        for d in data:
            for line in d["spectra_lines"]:
                for i, _ in enumerate(line):
                    line[i][1] = line[i][1] * (1 + noise_rate * random.random())

        return data
