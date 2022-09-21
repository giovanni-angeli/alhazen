# coding: utf-8

# pylint: disable=missing-docstring
# pylint: disable=invalid-name
# pylint: disable=logging-format-interpolation
# pylint: disable=logging-fstring-interpolation

import os
import logging
import asyncio
import shutil
import json
import traceback

from alhazen.compute_optical_constants import (compute_R, compute_T)

HERE = os.path.dirname(os.path.abspath(__file__))

DATA_TEMPLATES_PATH = os.path.join(HERE, "..", "..", "data_templates")
DATA_PATH = os.path.join(HERE, "..", "..", "__tmp__", "data")

STRUCTURE_FILES_PATH = os.path.join(DATA_PATH, "structure_files")
MEASURE_FILES_PATH = os.path.join(DATA_PATH, "measure_files")


class Backend:

    model_results = []

    def __init__(self, settings):

        self.settings = settings

        self.structure_file_list = os.listdir(STRUCTURE_FILES_PATH)
        self.measure_file_list = os.listdir(MEASURE_FILES_PATH)

        self.structure_file = self.structure_file_list[0] if self.structure_file_list else ''
        self.measure_file = self.measure_file_list[0] if self.measure_file_list else ''

        self._structure = {}
        self._measure = {}

        try:
            if self.structure_file:
                self.load_structure(self.structure_file)
            if self.measure_file:
                self.load_measure(self.measure_file)

        except BaseException:  # pylint: disable=broad-except

            logging.error(traceback.format_exc())

    async def run(self):

        while True:

            await asyncio.sleep(5)

    def install_templates(self):

        for p in (DATA_PATH, STRUCTURE_FILES_PATH, MEASURE_FILES_PATH):
            if not os.path.exists(p):
                os.makedirs(p)

        shutil.copytree(DATA_TEMPLATES_PATH, DATA_PATH, dirs_exist_ok=True)

        logging.info(f"structure_files:{os.listdir(STRUCTURE_FILES_PATH)}")
        logging.info(f"measure_files:{os.listdir(MEASURE_FILES_PATH)}")

    def load_structure(self, name):

        logging.info(f"name:{name}")

        pth = os.path.join(STRUCTURE_FILES_PATH, name)
        with open(pth, encoding='utf-8') as f:
            self._structure = json.load(f)
        self.structure_file = name

    def load_measure(self, name):

        logging.info(f"name:{name}")

        pth = os.path.join(MEASURE_FILES_PATH, name)
        with open(pth, encoding='utf-8') as f:
            self._measure = f.read()
        self.measure_file = name

    def refresh_model_data(self):

        data = []
        if self._structure:
            serie_R = compute_R(self._structure)
            serie_T = compute_T(self._structure)
            data.append(("R", serie_R))
            data.append(("T", serie_T))

        return data
