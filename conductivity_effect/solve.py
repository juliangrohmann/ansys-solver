import os.path
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

import materials.presets as sampling
from materials.presets import SampleMaterial
from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample, NodeContext


HEAT_LOADS = ['low', 'nominal', 'high2', 'high']

OUT_DIR = os.path.join(CURR_DIR, 'out')
INP_DIR = os.path.join(CURR_DIR, 'in')
NODES_DIR = os.path.join(PARENT_DIR, 'inp', 'nodes')
TOP_SURFACE_PATH = os.path.join(NODES_DIR, 'ts.node.loc')
BOTTOM_SURFACE_PATH = os.path.join(NODES_DIR, 'bs.node.loc')
ALL_LOCS_PATH = os.path.join(NODES_DIR, 'all.node.loc')


def sample_name(_conductivity, _structural, _plastic, _case):
    return f"{_conductivity.value}_{_structural.value}_{'plastic' if _plastic else 'elastic'}_{_case}"


def solve(names=None):
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

            if names is not None and sample.name not in names:
                continue

            sample.input = os.path.join(INP_DIR, f"{conductivity.value}_{case}.inp")
            sampling.set_structural(sample, structural, plastic)
            # sampling.add_pressure_loads(sample, structural, case)
            # sampling.add_thermal_loads(sample, structural, case)
            solver.add_sample(sample)

    solver.solve(verbose=False)
    return solver


if __name__ == '__main__':
    solve()
