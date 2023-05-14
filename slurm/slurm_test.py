import numpy as np
import sys
import os
import pkgutil
from ansys.mapdl import core as pymapdl

HOME = os.path.expanduser('~')
SCRATCH_PATH = os.path.join(HOME, 'scratch')
HEMJ_INP = os.path.join(SCRATCH_PATH, 'inp', 'hemj_v2.inp')
ANSYS_ROOT = os.environ['ANSYS_ROOT']
ANSYS_EXE = os.path.join(ANSYS_ROOT, 'v231', 'ansys', 'bin', 'ansys231')

sys.path.append(SCRATCH_PATH)

from parametric_solver.solver import BilinearSolver


print(f"Ansys executable = {ANSYS_EXE}")
pymapdl.change_default_ansys_path(ANSYS_EXE)

solver = BilinearSolver(HEMJ_INP)
solver.add_sample(200e9, 700e6, 70e9)
solver.solve()
