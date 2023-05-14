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


def find_ansys_directory(start_path):
    for root, dirs, _ in os.walk(start_path):
        if '.ansys' in dirs:
            return os.path.join(root, '.ansys')
    return None


SCRATCH_PATH = init_env()
# SCRATCH_PATH = r'D:\georgia_tech\diverters\src'
from parametric_solver.solver import BilinearSolver

HEMJ_INP = os.path.join(SCRATCH_PATH, 'inp', 'hemj_v2.inp')

# solver = BilinearSolver(HEMJ_INP)
# solver.add_sample(200e9, 700e6, 70e9)
# solver.solve()


start_path = os.path.expanduser('~')
ansys_dir = find_ansys_directory(start_path)

if ansys_dir:
    print(f"'.ansys' directory found at: {ansys_dir}")
else:
    print("'.ansys' directory not found.")
