import os.path
import sys
import numpy as np

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.join(CURR_DIR, '..')
sys.path.append(PARENT_DIR)

from parametric_solver.solver import BilinearSolver

# Initialize directories
INP_FILE = os.path.join(PARENT_DIR, 'inp', 'hemj_v2.inp')
OUT_DIR = os.path.join(CURR_DIR, 'out')

# Initialize sample ranges
elastic_mods = np.linspace(1e10, 6e10, 6)
yield_strengths = np.linspace(4.0e8, 6.5e8, 6)
tangent_mods = np.linspace(1.0e9, 2.0e9, 6)

# Add sample points to solver
solver = BilinearSolver(INP_FILE, write_path=OUT_DIR)
for elastic_mod in elastic_mods:
    for yield_strength in yield_strengths:
        for tangent_mod in tangent_mods:
            solver.add_sample(elastic_mod, yield_strength, tangent_mod)

# Solve at all sample points
solver.solve(verbose=True)
