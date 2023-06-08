import os.path
import sys
import numpy as np
import pyvista as pv

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

import materials.sampling as sampling
from materials.sampling import SampleMaterial
from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample, NodeContext
import linearization.surface as surface

HEAT_LOADS = ['low', 'nominal', 'high']

# Initialize directories
OUT_DIR = os.path.join(CURR_DIR, 'out')
INP_DIR = os.path.join(CURR_DIR, 'in')
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

for conductivity, structural, plastic in sims:
    for case in HEAT_LOADS:
        sample = BilinearThermalSample()
        sample.name = sample_name(conductivity, structural, plastic, case)
        sample.input = os.path.join(INP_DIR, f"{conductivity.value}_{case}.inp")
        sampling.set_structural(sample, structural, plastic)
        solver.add_sample(sample)

# Solve at all sample points
solver.solve(verbose=False)
