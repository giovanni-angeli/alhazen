# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-format-interpolation
# pylint: disable=logging-fstring-interpolation

import logging
import asyncio
import importlib
import pkgutil


class Backend:

    default_model_params = {
        '1st series': {'a': 1, 'b': 1, 'c': 1},
        '2nd series': {'a': 2, 'b': 2, 'c': 2},
        '3rd series': {'a': 4, 'b': 4, 'c': 4},
        '4th series': {'a': 8, 'b': 8, 'c': 8},
        '5th series': {'a': 0, 'b': 0.8, 'c': 0.08},
    }

    model_params = {}

    N0 = - 10
    N1 = 200

    model_results = []

    def __init__(self, settings):

        self.settings = settings
        self._model = None
        self.model_name = None

        self.alhazen_models = importlib.import_module("alhazen.models")
        self.alhazen_models_modules = {}

    async def run(self):

        model_list = self.list_models()
        logging.warning(f"model_list:{model_list}")

        if model_list:
            self.import_model(model_list[0])

        self.reset_model_params()
        while True:

            await asyncio.sleep(5)

    def list_models(self):

        model_list = [m.name for m in pkgutil.walk_packages(self.alhazen_models.__path__)]
        return model_list

    def import_model(self, model_name):

        logging.warning(f"dir(self.alhazen_models):{dir(self.alhazen_models)}")

        importlib.reload(self.alhazen_models)

        if self.alhazen_models_modules.get(model_name):
            importlib.reload(self.alhazen_models_modules[model_name])
        else:
            self.alhazen_models_modules[model_name] = importlib.import_module(f".{model_name}", "alhazen.models")

        self._model = self.alhazen_models_modules[model_name].Model()
        self.model_name = model_name
        self.model_description = str(self._model)
        logging.warning(f"self.model_name:{self.model_name}, self.__model:{self._model}")

    def reset_model_params(self):

        self.model_params = self.default_model_params.copy()
        logging.debug(f"self.model_params:{self.model_params}")

    def update_model_params(self, params):

        self.model_params.update(params)
        logging.debug(f"self.model_params:{self.model_params}")

    def refresh_model_data(self):

        data = []
        for k, params in self.model_params.items():

            logging.warning(f"params:{params}")

            serie = self._model.out_data(**params)
            data.append((k, serie))

        return data
