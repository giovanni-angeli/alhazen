# coding: utf-8

# pylint: disable=missing-docstring

import logging
import random
import math
import asyncio


class Backend:

    default_model_params = {
        '1st Line': {'a':  1, 'b':  1, 'c':  1},
        '2nd Line': {'a':  4, 'b':  4, 'c':  4},
        '3rd Line': {'a':  6, 'b':  6, 'c':  6},
        '4th Line': {'a':  8, 'b':  8, 'c':  8},
        '5th Line': {'a': 10, 'b': 10, 'c': 10},
    }

    model_results = []

    async def run(self):

        self.reset_model_params()
        while True:

            await asyncio.sleep(5)

    def model_distribution(self, x, a, b, c, N):

        return  .002 * a * x * random.random() + .1 * b * math.exp(x * 1/50.) + (10 + c) * math.exp(-1 * (x - N/(c + 1.))**2 * 0.2*c/N)

    def reset_model_params(self):

        self.model_params = self.default_model_params.copy()
        logging.info(f"self.model_params:{self.model_params}")

    def update_model_params(self, params):

        self.model_params.update(params)
        logging.info(f"self.model_params:{self.model_params}")

    def refresh_model_data(self):

        N0 = - 10
        N1 = 120

        data = []
        for k, p in self.model_params.items():
            data.append((k, [(i, self.model_distribution(i, p['a'], p['b'], p['c'], N1 - N0)) for i in range(N0, N1)]))

        return data

