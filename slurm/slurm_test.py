import numpy as np
import sys
import os
import pkgutil

home = os.path.expanduser('~')
sys.path.append(os.path.join(home, 'scratch'))

from parametric_solver.solver import BilinearSolver

print("TESTING")