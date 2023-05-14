import numpy as np
import sys
import os
import pkgutil

HOME = os.path.expanduser('~')
INP_PATH = sys.path.append(os.path.join(HOME, 'scratch', 'inp', 'hemj_v2.inp'))

from parametric_solver.solver import BilinearSolver


solver = BilinearSolver(INP_PATH)
solver.add_sample(200e9, 700e6, 70e9)
solver.solve()
