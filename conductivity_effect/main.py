import os.path
import sys
import numpy as np

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

import materials.sampling as sampling
from materials.sampling import SampleMaterial
from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample

HEAT_LOADS = ['low', 'nominal', 'high']

# Initialize directories
OUT_DIR = os.path.join(CURR_DIR, 'out')
INP_DIR = os.path.join(CURR_DIR, 'in')

# Add sample points to solver
solver = BilinearThermalSolver(write_path=OUT_DIR, loglevel="INFO")

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
        sample.name = f"{conductivity.value}_{structural.value}_{'plastic' if plastic else 'elastic'}_{case}"
        sample.input = os.path.join(INP_DIR, f"{conductivity.value}_{case}.inp")
        sampling.set_structural(sample, structural, plastic)
        solver.add_sample(sample)

# Solve at all sample points
solver.solve(verbose=False)

# nodeContext = NodeContext(os.path.join(INP_DIR, "kdoped_rhenium_high.inp"))
# nodeContext.add_component('cool_surf1')
# nodeContext.add_component('cool_surf2')
# nodeContext.run()
#
# print(len(nodeContext.nodes('cool_surf1')))
# print(len(nodeContext.nodes('cool_surf2')))
#
# nodes = nodeContext.nodes('cool_surf1') + nodeContext.nodes('cool_surf2')
# print(len(nodes))


def max_eqv_stresses(_conductivity, _structural, _plastic):
    max_stresses = []
    for _case in HEAT_LOADS:
        _result = solver.result_from_name(f"{_conductivity.value}_{_structural.value}_{'plastic' if _plastic else 'elastic'}_{_case}")
        max_stresses.append(max([_result.eqv_stress(node) for node in _result.valid_nodes()]))

    return max_stresses


for sim in sims:
    print(f"Conductivity: {sim[0].value}, Structural {sim[1].value}, {'plastic' if sim[2] else 'elastic'}")
    stresses = max_eqv_stresses(*sim)

    for case, stress in zip(HEAT_LOADS, stresses):
        print(f"{case}: {stress} MPa")

    print()
