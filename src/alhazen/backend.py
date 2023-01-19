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

from alhazen.compute_optical_properties import (compute_RT, compute_chi2, get_description)

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

        self.structure_file_list = [''] + os.listdir(STRUCTURE_FILES_PATH)
        self.measure_file_list = [''] + os.listdir(MEASURE_FILES_PATH)

        self.structure_file =  ''
        self.measure_file =  ''

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
        logging.info(f"name:{name}")

        self.structure_file = name
        self._structure = {}
        if name:
            pth = os.path.join(STRUCTURE_FILES_PATH, name)
            with open(pth, encoding='utf-8') as f:
                self._structure = json.load(f)

    def load_measure(self, name=None):

        # AUGH: mi sfugge il gioco tra "name" e "self.measure_file" qui ...
        if name is None and self.measure_file != 'None':
            name = self.measure_file
        logging.info(f"name:{name}")

        self._measure = []
        # AUGH: ... e qui (BTW, l'istruzione qui di seguito starebbe meglio
        # dentro l'if).
        self.measure_file = name
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
                        # FIXME: may/should have more columns containing
                        # measuerement errors
                        self._measure[0].append((l, R))
                        self._measure[1].append((l, T))

    def refresh_model_data(self, params):
        # TODO: backend should call different functions depending on actions
        # from frontend (*); "data" should be "variable" in the sense that it
        # may represent different stuff: it is better to put it in a self
        # descriptive form (dict?).
        # (*) or maybe frontend should call different backend functions
        # TODO: the name "refresh_model_data" can be non convenient: it
        # should be "compute something"

        show_R = True if params.get('plot_edit_panel').get('show_R') else False
        show_T = True if params.get('plot_edit_panel').get('show_T') else False
        show_A = True if params.get('plot_edit_panel').get('show_A') else False

        data = []
        if self._structure:
            serie_R,serie_T = compute_RT(self._structure, params)
            if show_R: data.append(("Rc", serie_R))
            if show_T: data.append(("Tc", serie_T))
            if show_A:
                serie_A = []
                for R,T in zip(serie_R,serie_T):
                    serie_A.append( (R[0], 100-(R[1]+T[1])) )
                data.append(("Ac", serie_A))

        if self._measure:
            if show_R: data.append(("Re", self._measure[0]))
            if show_T: data.append(("Te", self._measure[1]))
            if show_A:
                serie_A = []
                for R,T in zip(self._measure[0],self._measure[1]):
                    serie_A.append( (R[0], 100-(R[1]+T[1])) )
                data.append(("Ae", serie_A))


        chi2 = None
        if self._structure and self._measure:
            chi2 = compute_chi2(self._structure, self._measure, params)

        message = get_description(self._structure, params)

        return data, chi2, message

