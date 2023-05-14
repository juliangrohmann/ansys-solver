import sys
import os
from ansys.mapdl import core as pymapdl


def init_env():
    home = os.path.expanduser('~')
    scratch_path = os.path.join(home, 'scratch')
    sys.path.append(scratch_path)

    ansys_root = os.environ['ANSYS_ROOT']
    ansys_exe = os.path.join(ansys_root, 'v231', 'ansys', 'bin', 'ansys231')
    print(f"Setting ANSYS executable path: {ansys_exe}")
    pymapdl.change_default_ansys_path(ansys_exe)

    return scratch_path


# SCRATCH_PATH = init_env()
SCRATCH_PATH = r'D:\georgia_tech\diverters\src'
from parametric_solver.solver import BilinearSolver


HEMJ_INP = os.path.join(SCRATCH_PATH, 'inp', 'hemj_v2.inp')
print(os.getenv("TEMP"))
# solver = BilinearSolver(HEMJ_INP)
# solver.add_sample(200e9, 700e6, 70e9)
# solver.solve()
