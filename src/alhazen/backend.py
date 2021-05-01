# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-format-interpolation

import os
import asyncio
import json
import logging
import random
import math


class Backend:

    default_params = {
        'start': {
            'value': 0,
            'description': "first line of data to graph",
            "type": "int",
            'min':0,
            'max':10,
        },
        'stop': {
            'value': 3,
            'description': "last line of data to graph",
            "type": "int",
            'min':0,
            'max':10,
        },
        'noise_rate': {
            'value': 0.1,
            'description': "",
            "type": "float",
            'min':0,
            'max':10.,
        },
        'data_file': {
            'value': "./test/fixtures/samples.json",
            'description': "",
            "type": "str",
        },
    }

    params = {}
    params_file_path = "./alhazen.params.json"
    title = 'plot example - intensity(%) vs wavelength(nm)'

    async def run(self):

        self.reset_params()
        self.load_params_from_json_file()

        while True:

            await asyncio.sleep(5)

    def reset_params(self):

        self.params = self.default_params.copy()

    def update_params(self, params):

        self.params.update(params)

    def dump_params_to_json_file(self):

        logging.info(f"self.params_file_path:{self.params_file_path}")

        with open(self.params_file_path, 'w') as f:
            json.dump(self.params, f, indent=2)

    def load_params_from_json_file(self):

        logging.info(f"self.params_file_path:{self.params_file_path}")

        if os.path.exists(self.params_file_path):
            with open(self.params_file_path) as f:
                self.params = json.load(f)

    def load_data_from_json_file(self):

        data_file = self.params['data_file']['value']

        logging.info(f"data_file:{data_file}")

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
                for i, k in enumerate(line):
                    line[i][1] = line[i][1] * (1 + noise_rate * random.random())

        return data
