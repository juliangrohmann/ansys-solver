import numpy as np
import sys
import os
import pkgutil

HOME = os.path.expanduser('~')
INP_PATH = os.path.join(HOME, 'scratch', 'inp')
HEMJ_INP = os.path.join(INP_PATH, "hemj_v2.inp")

sys.path.append(INP_PATH)

from parametric_solver.solver import BilinearSolver


solver = BilinearSolver(HEMJ_INP)
solver.add_sample(200e9, 700e6, 70e9)
solver.solve()
