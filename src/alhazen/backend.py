# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-format-interpolation
# pylint: disable=logging-fstring-interpolation

import logging
import random
import math
import asyncio


class Backend:

    default_model_params = {
        '1st Line': {'a': 1, 'b': 1, 'c': 1},
        '2nd Line': {'a': 2, 'b': 2, 'c': 2},
        '3rd Line': {'a': 4, 'b': 4, 'c': 4},
        '4th Line': {'a': 8, 'b': 8, 'c': 8},
    }

    model_params = {}

    N0 = - 10
    N1 = 180

    model_results = []

    def __init__(self, settings):

        self.settings = settings

    async def run(self):

        self.reset_model_params()
        while True:

            await asyncio.sleep(5)

    def reset_model_params(self):

        self.model_params = self.default_model_params.copy()
        logging.debug(f"self.model_params:{self.model_params}")

    def update_model_params(self, params):

        self.model_params.update(params)
        logging.debug(f"self.model_params:{self.model_params}")

    def refresh_model_data(self):

        data = []

        def model_distribution(x, a, b, c, N):

            y = 0
            y += .002 * a * x * random.random()
            y += (5 / N) * b * math.exp(x * 0.02)
            y += 10. * (1 + c) * math.exp(-1 * (x - N / (c + 1.))**2 * 0.002 * c)

            return y

        def map_(i, p):
            return model_distribution(i, p['a'], p['b'], p['c'], (self.N1 + self.N0) / 2)

        for k, p in self.model_params.items():

            serie = [(i, map_(i, p)) for i in range(self.N0, self.N1)]
            data.append((k, serie))

        return data
