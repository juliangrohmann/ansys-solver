import math
import numpy as np

from parametric_solver.linearization import APDLIntegrate


class APDLResult:
    """
    Wrapper class for an MAPDL result. Stores stress and strain data at all nodes.
    Provides access to linearization.

    Will be pickled or loaded to/from storage by solvers.
    """
    def __init__(self, result, i=None):
        """
        Parses nodal stress/strain data from the MAPDL result and maps it to a dictionary.

        Parameters
        ----------
        result: ansys.mapdl.reader.rst.Result
            PyMAPDL result that will be wrapped by this class.

        i: int, optional
            The timestep of the result that will be stored.
            If None, will default to final timestep.

        Notes
        -----
        Used internally by solvers.
        """
        if not i:
            i = result.n_results - 1

        self.stress = {}
        self.elastic_strain = {}
        self.plastic_strain = {}
        self.displacement = {}

        stress_raw = result.nodal_stress(i)
        elastic_strain_raw = result.nodal_elastic_strain(i)

        try:
            plastic_strain_raw = result.nodal_plastic_strain(i)
        except ValueError:
            print("No plastic strain data available!")
            plastic_strain_raw = None

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

        if plastic_strain_raw:
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
        """
        Evaluates the equivalent (von Mises) stress at a node.

        Parameters
        ----------
        node: int
            The id of the node

        Returns
        -------
        float
            The equivalent (von Mises) stress at the given node.
        """
        flat_stress = self.stress_tensor(node)
        return von_mises(flat_stress)

    def stress_tensor(self, node):
        """
        Evaluates the stress tensor at a node.

        Parameters
        ----------
        node: int
            The id of the node

        Returns
        -------
        np.array
            A 1x6 array holding the components of the stress tensor in the following order:
            [xx, yy, zz, xy, yz, xz]
        """
        return _flatten_tensor(_map_to_tensor(self.stress, node))

    def linearized_stress_tensor(self, nodes, locations, averaged=True):
        """
        Evaluates the linearized stress tensor across a series of nodes.

        Parameters
        ----------
        nodes: list<int>
            The ids of the nodes across which to linearize.

        locations: np.ndarry<float>
            A (n x 3) array holding the coordinates of the nodes across which to linearize,
            where n is the amount of nodes.

        averaged: bool
            If True, averages the tensors across the given nodes,
            otherwise returns the tensor at each nodes.

        Returns
        -------
        If averaged=True: np.ndarray
            A (n x 6) array, in which each row holds the components of the stress tensor at that node.
            Components are in the following order:
            [xx, yy, zz, xy, yz, xz]

        If averaged=False: np.ndarray
            A (1 x 6) array holding the components of the stress tensor, averaged across the given nodes.
            Components are in the following order:
            [xx, yy, zz, xy, yz, xz]

        Notes
        -----
        Linearization is performed according to ASME guidelines.
        """
        stress = np.array([self.stress_tensor(node) for node in nodes])
        return _linearize(stress, locations, len(nodes), averaged=averaged)

    def total_strain(self, node):
        """
        Evaluates the total strain at a node.

        Parameters
        ----------
        node: int
            The id of the node

        Returns
        -------
        float
            The total strain at the given node.
        """
        plastic_strain = self.plastic_strain[node]["EQV"] if node in self.plastic_strain else 0
        return self.elastic_strain[node]["EQV"] + plastic_strain

    def strain_tensor(self, node):
        """
        Returns the strain tensor at a node.

        Parameters
        ----------
        node: int
            The id of the node

        Returns
        -------
        np.ndarray
            A 1x6 array holding the components of the strain tensor in the following order:
            [xx, yy, zz, xy, yz, xz]
        """

        elastic = np.array(_flatten_tensor(_map_to_tensor(self.elastic_strain, node)))

        if node not in self.plastic_strain:
            return elastic
        else:
            plastic = np.array(_flatten_tensor(_map_to_tensor(self.plastic_strain, node)))
            return elastic + plastic

    def linearized_strain_tensor(self, nodes, locations, averaged=True):
        """
        Evaluates the linearized strain tensor across a series of nodes.

        Parameters
        ----------
        nodes: list<int>
            The ids of the nodes across which to linearize.

        locations: np.ndarry<float>
            A (n x 3) array holding the coordinates of the nodes across which to linearize,
            where n is the amount of nodes.

        averaged: bool
            If True, averages the tensors across the given nodes,
            otherwise returns the tensor at each nodes.

        Returns
        -------
        If averaged=True: np.ndarray
            A (n x 6) array, in which each row holds the components of the strain tensor at that node.
            Components are in the following order:
            [xx, yy, zz, xy, yz, xz]

        If averaged=False: np.ndarray
            A (1 x 6) array holding the components of the strain tensor, averaged across the given nodes.
            Components are in the following order:
            [xx, yy, zz, xy, yz, xz]

        Notes
        -----
        Linearization is performed according to ASME guidelines.
        """
        strain = np.array([self.strain_tensor(node) for node in nodes])
        return _linearize(strain, locations, len(nodes), averaged=averaged)

    def valid_nodes(self):
        """
        Retrieves the ids of all nodes at which a result is available.

        Returns
        -------
        list<int>
            A list holding the ids of all nodes that have a valid result.

        Notes
        -----
        Nodes without a result are midpoint nodes that are only used during solving.
        """
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
