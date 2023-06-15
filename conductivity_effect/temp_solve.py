import os.path
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

import materials.sampling as sampling
from materials.sampling import SampleMaterial
from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample, NodeContext

HEAT_LOADS = ['low', 'nominal', 'high']

# Initialize directories
OUT_DIR = os.path.join(CURR_DIR, 'out', 'temp_interp', 'kdoped_rhenium')
INP_DIR = os.path.join(CURR_DIR, 'in', 'temp_interp', 'kdoped_rhenium', 'inp')
NODES_DIR = os.path.join(PARENT_DIR, 'inp', 'nodes')
TOP_SURFACE_PATH = os.path.join(NODES_DIR, 'ts.node.loc')
BOTTOM_SURFACE_PATH = os.path.join(NODES_DIR, 'bs.node.loc')
ALL_LOCS_PATH = os.path.join(NODES_DIR, 'all.node.loc')


def sample_name(_conductivity, _structural, _plastic, _case):
    return f"{_conductivity.value}_{_structural.value}_{'plastic' if _plastic else 'elastic'}_{_case}"


# Add sample points to solver
solver = BilinearThermalSolver(write_path=OUT_DIR, loglevel="INFO", nproc=8)

sims = [
    (SampleMaterial.W_3RHENIUM, SampleMaterial.W_3RHENIUM, False),
    (SampleMaterial.WL10, SampleMaterial.WL10, False),
    (SampleMaterial.WL10, SampleMaterial.PURE_W, False),
    (SampleMaterial.W_3RHENIUM, SampleMaterial.W_3RHENIUM, True),
    (SampleMaterial.WL10, SampleMaterial.PURE_W, True)
]

for i in range(8, 10):
    sample = BilinearThermalSample()
    sample.name = f"kdoped_rhenium_{i}"
    sample.input = os.path.join(INP_DIR, f"{sample.name}.inp")
    sampling.set_structural(sample, SampleMaterial.W_3RHENIUM, True)
    solver.add_sample(sample)

# Solve at all sample points
solver.solve(verbose=True)
