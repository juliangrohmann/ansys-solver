import numpy as np
import sys
import os
import pkgutil

HOME = os.path.expanduser('~')
SCRATCH_PATH = os.path.join(HOME, 'scratch')
HEMJ_INP = os.path.join(SCRATCH_PATH, 'inp', 'hemj_v2.inp')
ANSYS_ROOT = os.environ['ANSYS_ROOT']
ANSYS_EXE = os.path.join(ANSYS_ROOT, 'v231', 'ansys', 'bin', 'ansys231')

sys.path.append(SCRATCH_PATH)

from parametric_solver.solver import BilinearSolver


def print_directory_tree(start_path):
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * level
        print(f'{indent}{os.path.basename(root)}/')
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            print(f'{sub_indent}{f}')


print(f"ANSYS ROOT = {ANSYS_ROOT}")
print_directory_tree(ANSYS_ROOT)

# solver = BilinearSolver(HEMJ_INP)
# solver.add_sample(200e9, 700e6, 70e9)
# solver.solve()
