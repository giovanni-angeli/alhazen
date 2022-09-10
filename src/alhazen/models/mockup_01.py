# -*- coding: utf-8 -*-

# pylint: disable=missing-docstring
# pylint: disable=logging-format-interpolation
# pylint: disable=line-too-long
# pylint: disable=invalid-name
# pylint: disable=too-many-lines
# pylint: disable=consider-using-f-string
# pylint: disable=logging-fstring-interpolation

import logging
import random
import math


class Model:

    K0 = .05
    K1 = 0.005
    K2 = .5
    K3 = 0.02
    K4 = 0.02

    N0 = - 10
    N1 = 200

    def __str__(self):

        return f"""<h3><span style="color:blue;">modello 01</span> - K0:{self.K0}, K1:{self.K1}, K2:{self.K2}, K3:{self.K3}, K4:{self.K4}.</h3>"""

    def map_(self, x, n, a, b, c):

        y = n * (math.sin(self.K0 * a * x) + math.cos(self.K1 * b * x) + math.tan(self.K2 * c * x))
        return y

    def out_data(self, a=0, b=0, c=0):

        N = (self.N1 + self.N0) / 2
        out_data = [(i, self.map_(i, N, a, b, c)) for i in range(self.N0, self.N1)]
        return out_data 
