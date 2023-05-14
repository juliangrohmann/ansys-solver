import numpy as np
import sys
import os
import pkgutil

HOME = os.path.expanduser('~')
SCRATCH_PATH = os.path.join(HOME, 'scratch')
HEMJ_INP = os.path.join(SCRATCH_PATH, 'inp', 'hemj_v2.inp')

sys.path.append(SCRATCH_PATH)

from parametric_solver.solver import BilinearSolver


solver = BilinearSolver(HEMJ_INP)
solver.add_sample(200e9, 700e6, 70e9)
solver.solve()
