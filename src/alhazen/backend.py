# coding: utf-8

# pylint: disable=missing-docstring

import logging
import random
import math
import asyncio


class Backend:

    default_model_params = {
        'One  ': {'a': 1, 'b': 1, 'c': 5.1},
        'Two  ': {'a': 2, 'b': 2, 'c': 5.2},
        'Three': {'a': 3, 'b': 3, 'c': 5.3},
        'Four ': {'a': 4, 'b': 4, 'c': 5.4},
        'Five ': {'a': 5, 'b': 5, 'c': 5.5},
    }

    model_results = []

    async def run(self):

        self.reset_model_params()
        while True:

            await asyncio.sleep(5)
            # ~ logging.info(f"self.context:{self.context}")

    def model_distribution(self, x, a, b, c):

        return  10. * a * x * random.random() + b * x * x + math.exp(c/50. * x)

    def reset_model_params(self):

        self.model_params = self.default_model_params.copy()
        logging.info(f"self.model_params:{self.model_params}")

    def update_model_params(self, params):

        self.model_params.update(params)
        logging.info(f"self.model_params:{self.model_params}")

    def refresh_model_data(self):

        N = 100

        data = []
        for k, p in self.model_params.items():
            data.append((k, [(i, self.model_distribution(i, p['a'], p['b'], p['c'])) for i in range(N)]))

        return data

