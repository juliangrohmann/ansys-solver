import os.path
import sys
import math
import numpy as np
import pandas as pd

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

import linearization.surface as surface
import linearization.linearization as linearization


NODES_DIR = os.path.join(PARENT_DIR, 'inp', 'nodes')
_TOP_SURFACE_PATH = os.path.join(NODES_DIR, 'ts.node.loc')
_BOTTOM_SURFACE_PATH = os.path.join(NODES_DIR, 'bs.node.loc')
_ALL_LOCS_PATH = os.path.join(NODES_DIR, 'all.node.loc')


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

        if plastic_strain_raw is not None:
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

    def stress_dataframe(self):
        return self._dict_to_dataframe(self.stress)

    def strain_dataframe(self):
        strain_df = self._dict_to_dataframe(self.elastic_strain)

        if self.plastic_strain:
            plastic_df = self._dict_to_dataframe(self.plastic_strain)
            strain_df = strain_df.add(plastic_df)

        return strain_df

    def _dict_to_dataframe(self, data):
        rows = []

        for node in self.valid_nodes():
            value = data[node]
            if "EQV" in value:
                rows.append(pd.Series([value["X"], value["Y"], value["Z"], value["XY"], value["YZ"], value["XZ"], value["EQV"]], name=node))
            else:
                rows.append(pd.Series([value["X"], value["Y"], value["Z"], value["XY"], value["YZ"], value["XZ"]], name=node))

        return pd.DataFrame(rows)

    def linearized_stress_result(self):
        dataframe = self.stress_dataframe()

        return surface.linearize_surface(
            _TOP_SURFACE_PATH,
            _BOTTOM_SURFACE_PATH,
            dataframe,
            _ALL_LOCS_PATH,
            None,
            False
        )

    def linearized_strain_result(self):
        dataframe = self.strain_dataframe()
        dataframe = dataframe.drop(dataframe.columns[6], axis=1)

        return surface.linearize_surface(
            _TOP_SURFACE_PATH,
            _BOTTOM_SURFACE_PATH,
            dataframe,
            _ALL_LOCS_PATH,
            None,
            True
        )

    def max_linearized_stresses(self):
        lin_result = self.linearized_stress_result()
        return {
            'membrane': max(lin_result['membrane']),
            'bending': max(lin_result['bending']),
            'linearized': max(lin_result['membrane'] + lin_result['bending'])
        }

    def max_linearized_strains(self):
        lin_result = self.linearized_strain_result()
        return {
            'membrane': max(lin_result['membrane']),
            'bending': max(lin_result['bending']),
            'linearized': max(lin_result['membrane'] + lin_result['bending'])
        }

    def max_eqv_stress(self, nodes=None):
        stress_df = self.stress_dataframe()

        if nodes is not None:
            stress_df = stress_df[stress_df.index.isin(nodes)]

        eqv_stress = linearization.von_mises(stress_df.values)
        return max(eqv_stress)

    def max_eqv_strain(self, nodes=None):
        strain_df = self.strain_dataframe()
        strain_df = strain_df.drop(strain_df.columns[6], axis=1)

        if nodes is not None:
            strain_df = strain_df[strain_df.index.isin(nodes)]

        eqv_stress = linearization.von_mises_strain(strain_df.values)
        return max(eqv_stress)


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
    num = (tensor[0] - tensor[1]) ** 2 + \
          (tensor[1] - tensor[2]) ** 2 + \
          (tensor[2] - tensor[0]) ** 2 + \
          6 * (tensor[3] ** 2 + tensor[4] ** 2 + tensor[5] ** 2)

    return (num / 2) ** 0.5
