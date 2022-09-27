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
import csv

from alhazen.compute_optical_constants import (compute_RT, get_description)

HERE = os.path.dirname(os.path.abspath(__file__))

DATA_TEMPLATES_PATH = os.path.join(HERE, "..", "..", "data_templates")
DATA_PATH = os.path.join(HERE, "..", "..", "__tmp__", "data")

STRUCTURE_FILES_PATH = os.path.join(DATA_PATH, "structure_files")
MEASURE_FILES_PATH = os.path.join(DATA_PATH, "measure_files")


class Backend:

    model_results = []

    def __init__(self, settings):

        self.settings = settings

        for p in (DATA_PATH, STRUCTURE_FILES_PATH, MEASURE_FILES_PATH):
            if not os.path.exists(p):
                os.makedirs(p, exist_ok=True)

        self.structure_file_list = os.listdir(STRUCTURE_FILES_PATH)
        self.measure_file_list = os.listdir(MEASURE_FILES_PATH)

        self.structure_file = self.structure_file_list[0] if self.structure_file_list else ''
        self.measure_file = self.measure_file_list[0] if self.measure_file_list else ''

        logging.info(f"self.structure_file_list:{self.structure_file_list}.")
        logging.info(f"self.measure_file_list  :{self.measure_file_list}  .")
        logging.info(f"self.structure_file:{self.structure_file}.")
        logging.info(f"self.measure_file  :{self.measure_file  }.")

        self._structure = {}
        self._measure = []

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

        shutil.copytree(DATA_TEMPLATES_PATH, DATA_PATH, dirs_exist_ok=True)

        logging.info(f"structure_files:{os.listdir(STRUCTURE_FILES_PATH)}")
        logging.info(f"measure_files:{os.listdir(MEASURE_FILES_PATH)}")

    def load_structure(self, name=None):

        if name is None and self.structure_file != 'None':
            name = self.structure_file
        else:
            # questo dovrebbe rimuovere _structure da self
            delattr( self, '_structure' )
            # qusto dovrebe uscire senza popolare _structure
            return
        logging.info(f"name:{name}")

        if name:
            pth = os.path.join(STRUCTURE_FILES_PATH, name)
            with open(pth, encoding='utf-8') as f:
                self._structure = json.load(f)
            self.structure_file = name

    def load_measure(self, name=None):

        if name is None and self.measure_file != 'None':
            name = self.measure_file
        else:
            # questo dovrebbe rimuovere _measure da self
            delattr( self, '_measure' )
            # qusto dovrebe uscire senza popolare _measure
            return
        logging.info(f"name:{name}")

        if name:
            self._measure = [[], []]
            pth = os.path.join(MEASURE_FILES_PATH, name)
            with open(pth, encoding='utf-8') as f:
                for i, row in enumerate(csv.reader(f)):
                    if i == 0:
                        pass
                    else:
                        l = float(row[0])
                        R = float(row[1])
                        T = float(row[2])
                        self._measure[0].append((l, R))
                        self._measure[1].append((l, T))

            self.measure_file = name

    def refresh_model_data(self, params):

        data = []
        if self._structure:
            serie_R,serie_T = compute_RT(self._structure, params)
            data.append(("Rc", serie_R))
            data.append(("Tc", serie_T))

        if self._measure:
            data.append(("Re", self._measure[0]))
            data.append(("Te", self._measure[1]))

        message = get_description(self._structure, params)

        return data, message

