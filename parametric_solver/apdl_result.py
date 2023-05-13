import math
import numpy as np

from parametric_solver.linearization import APDLIntegrate


class APDLResult:
    def __init__(self, result, i=None):
        if not i:
            i = result.n_results - 1

        self.stress = {}
        self.elastic_strain = {}
        self.plastic_strain = {}
        self.displacement = {}

        stress_raw = result.nodal_stress(i)
        elastic_strain_raw = result.nodal_elastic_strain(i)
        plastic_strain_raw = result.nodal_plastic_strain(i)

        for data in zip(stress_raw[0], stress_raw[1]):
            self.stress[data[0]] = {
                "X": data[1][0],
                "Y": data[1][1],
                "Z": data[1][2],
                "XY": data[1][3],
                "YZ": data[1][4],
                "XZ": data[1][5]
            }
        for data in zip(elastic_strain_raw[0], elastic_strain_raw[1]):
            self.elastic_strain[data[0]] = {
                "X": data[1][0],
                "Y": data[1][1],
                "Z": data[1][2],
                "XY": data[1][3],
                "YZ": data[1][4],
                "XZ": data[1][5],
                "EQV": data[1][6]
            }
        for data in zip(plastic_strain_raw[0], plastic_strain_raw[1]):
            self.plastic_strain[data[0]] = {
                "X": data[1][0],
                "Y": data[1][1],
                "Z": data[1][2],
                "XY": data[1][3],
                "YZ": data[1][4],
                "XZ": data[1][5],
                "EQV": data[1][6]
            }

    def eqv_stress(self, node):
        flat_stress = self.stress_tensor(node)
        return von_mises(flat_stress)

    def stress_tensor(self, node):
        return _flatten_tensor(_map_to_tensor(self.stress, node))

    def linearized_stress_tensor(self, nodes, locations, averaged=True):
        stress = np.array([self.stress_tensor(node) for node in nodes])
        return _linearize(stress, locations, len(nodes), averaged=averaged)

    def total_strain(self, node):
        return self.elastic_strain[node]["EQV"] + self.plastic_strain[node]["EQV"]

    def strain_tensor(self, node):
        elastic = np.array(_flatten_tensor(_map_to_tensor(self.elastic_strain, node)))
        plastic = np.array(_flatten_tensor(_map_to_tensor(self.plastic_strain, node)))
        return elastic + plastic

    def linearized_strain_tensor(self, nodes, locations, averaged=True):
        strain = np.array([self.strain_tensor(node) for node in nodes])
        return _linearize(strain, locations, len(nodes), averaged=averaged)

    def valid_nodes(self):
        return [node for node in self.stress if not math.isnan(self.stress[node]["X"])]


def _linearize(vals, locations, n, averaged=True):
    membrane = APDLIntegrate(vals, locations, n).membrane_tensor(averaged=averaged)[0]
    bending = APDLIntegrate(vals, locations, n).bending_tensor(averaged=averaged)[0]

    if averaged:
        return membrane + bending

    tensors = []
    for i in range(n):
        mem_tensor = np.array([membrane[j][i] for j in range(6)])
        ben_tensor = np.array([bending[j][i] for j in range(6)])
        tensor = np.array(mem_tensor + ben_tensor)
        tensors.append(tensor)

    return tensors


def _flatten_tensor(tensor):
    return np.array([tensor[0][0], tensor[1][1], tensor[2][2], tensor[0][1], tensor[1][2], tensor[0][2]])


def _map_to_tensor(result_map, node):
    return [[result_map[node]["X"], result_map[node]["XY"], result_map[node]["XZ"]],
            [result_map[node]["XY"], result_map[node]["Y"], result_map[node]["YZ"]],
            [result_map[node]["XZ"], result_map[node]["YZ"], result_map[node]["Z"]]]


def _distance(pos1, pos2):
    return ((pos1[0] - pos2[0]) ** 2 +
            (pos1[1] - pos2[1]) ** 2 +
            (pos1[2] - pos2[2]) ** 2) ** 0.5


def von_mises(tensor):
    if len(tensor.shape) == 1 or tensor.shape[0] == 1 or tensor.shape[1] == 1:
        num = (tensor[0] - tensor[1]) ** 2 + \
              (tensor[1] - tensor[2]) ** 2 + \
              (tensor[2] - tensor[0]) ** 2 + \
              6 * (tensor[3] ** 2 + tensor[4] ** 2 + tensor[5] ** 2)
    else:
        num = (tensor[0][0] - tensor[1][1]) ** 2 + \
              (tensor[1][1] - tensor[2][2]) ** 2 + \
              (tensor[2][2] - tensor[0][0]) ** 2 + \
              6 * (tensor[0][1] ** 2 + tensor[1][2] ** 2 + tensor[2][0] ** 2)

    return (num / 2) ** 0.5
