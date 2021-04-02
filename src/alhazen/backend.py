# coding: utf-8

# pylint: disable=missing-docstring

import logging
import asyncio

class Backend:

    model_params = {
        'P1': 1,
        'P2': 2,
        'P3': 3,
    }

    model_results = []

    async def run(self):

        while 1:

            await asyncio.sleep(5)
            logging.info(f"self.context:{self.context}") 

    def refresh_model_results(self):

        p1, p2, p3 = self.model_params.values()

        self.model_results = []
        for i in range(10):
            self.model_results.append((i, p1 + i*p2 + i*i*p3))

