import os.path
import sys
import numpy as np
import matplotlib.pyplot as plt
import parametric_solver.apdl_result as apdl_result
import pickle

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


def get_result(_conductivity, _structural, _plastic, _case):
    return solver.result_from_name(f"{_conductivity.value}_{_structural.value}_{'plastic' if _plastic else 'elastic'}_{_case}")


def max_eqv_stresses(_conductivity, _structural, _plastic):
    max_stresses = []
    for _case in HEAT_LOADS:
        _result = solver.result_from_name(f"{_conductivity.value}_{_structural.value}_{'plastic' if _plastic else 'elastic'}_{_case}")
        max_stresses.append(max([_result.eqv_stress(node) for node in _result.valid_nodes()]))

    return max_stresses


def read_node_data():
    node_data = []
    with open("D:\\projects\\diverters\\src\\results\\hemj_v2\\line_nodes_side.txt") as f:
        for line in f:
            try:
                data = line.split()
                node_data.append([int(data[0]), float(data[1]), float(data[2]), float(data[3])])
            except ValueError:
                continue
    node_data.sort(key=lambda x: x[3])
    return node_data


def eval_linear_stress(_result, node_data):
    nodes = [data[0] for data in node_data]
    positions = np.array([[data[1], data[2], data[3]] for data in node_data])
    linear_stresses = _result.linearized_stress_tensor(nodes, positions)
    linear_von_mises = [tensor for tensor in linear_stresses]
    return max(linear_von_mises)


node_id_data = read_node_data()

eqv_stress_data = []
lin_stress_data = []
for sim in sims:
    print(f"Conductivity: {sim[0].value}, Structural {sim[1].value}, {'plastic' if sim[2] else 'elastic'}")
    stresses = max_eqv_stresses(*sim)

    sim_eqv_data = []
    sim_lin_data = []
    for case, stress in zip(HEAT_LOADS, stresses):
        sim_eqv_data.append(stress)
        print(f"{case}: {stress} MPa")

        result = get_result(sim[0], sim[1], sim[2], case)
        sim_lin_data.append(eval_linear_stress(result, node_id_data))

    eqv_stress_data.append(sim_eqv_data)
    lin_stress_data.append(sim_lin_data)
    print()


print(eqv_stress_data)
print(lin_stress_data)

labels = ['3% Re, 3% Re (E)', 'WL10, WL10 (E)', 'WL10, W (E)', '3% Re, 3% Re (P)', 'WL10, W (P)']
bar_width = 0.25
spacing = 0.3
data = lin_stress_data
indexes = np.arange(len(data))

for i in range(3):
    plt.bar(indexes + i * bar_width, [item[i] for item in data], bar_width)

plt.xticks(indexes + bar_width, labels)
plt.xticks(rotation=45)
plt.subplots_adjust(bottom=0.5)
# plt.xticks(indexes + bar_width, ['G' + str(i + 1) for i in range(len(eqv_stress_data))])
plt.show()