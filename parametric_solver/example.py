import numpy as np
from solver import BilinearSolver


INP_FILE = r"D:\georgia_tech\diverters\src\parametric_solver\in\hemj_test.inp"
OUT_DIR = r"D:\georgia_tech\diverters\src\parametric_solver\out"


# Initialize sample ranges
elastic_mods = np.linspace(1e10, 6e10, 6)
yield_strengths = np.linspace(4.0e8, 6.5e8, 6)
tangent_mods = np.linspace(1.0e9, 2.0e9, 6)

# Add sample points to solver
solver = BilinearSolver(INP_FILE)
for elastic_mod in elastic_mods:
    for yield_strength in yield_strengths:
        for tangent_mod in tangent_mods:
            solver.add_sample(elastic_mod, yield_strength, tangent_mod)

# Solve at all sample points
solver.solve(write_path=OUT_DIR, verbose=True)
