# -*- coding: utf-8 -*-

# pylint: disable=missing-docstring
# pylint: disable=logging-format-interpolation
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=too-many-lines
# pylint: disable=consider-using-f-string
# pylint: disable=logging-fstring-interpolation

import random


class Model:

    def __str__(self):

        return """<h3><span style="color:#EE9900;">modello 00</span>.</h3>"""

    def out_data(self, a=0, b=0, c=0):

        out_data = [(i, a + b * i + c * random.random()) for i in range(100)]
        return out_data 
