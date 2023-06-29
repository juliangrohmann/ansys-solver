import os.path
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample
from parametric_solver.util import plot_eqv_stress


OUT_DIR = os.path.join(PARENT_DIR, 'analysis_v1', 'out')


solver = BilinearThermalSolver(write_path=OUT_DIR, loglevel="INFO", nproc=8)

sample = BilinearThermalSample()
sample.name = "wl10_idx3"
solver.add_sample(sample)
solver.solve(verbose=True)

result = solver.result_from_name(sample.name)
plot_eqv_stress(result)
