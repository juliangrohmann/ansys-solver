import os.path
import sys
import math
import numpy as np
import pandas as pd
import time

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

import linearization.surface as surface
import linearization.linearization as linearization


NODES_DIR = os.path.join(PARENT_DIR, 'inp', 'nodes')
_TOP_SURFACE_PATH = os.path.join(NODES_DIR, 'ts.node.loc')
_BOTTOM_SURFACE_PATH = os.path.join(NODES_DIR, 'bs.node.loc')
_ALL_LOCS_PATH = os.path.join(NODES_DIR, 'all.node.loc')

_FLAT_TOP_SURFACE_PATH = os.path.join(NODES_DIR, 'ts_flat.node.loc')
_FLAT_BOTTOM_SURFACE_PATH = os.path.join(NODES_DIR, 'bs_flat.node.loc')
_FLAT_ALL_LOCS_PATH = os.path.join(NODES_DIR, 'all_flat.node.loc')

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


        # self.stress = None
        # self.elastic_strain = None
        # self.plastic_strain = None

        # stress_raw = result.nodal_stress(i)
        # elastic_strain_raw = result.nodal_elastic_strain(i)

        # try:
        #     plastic_strain_raw = result.nodal_plastic_strain(i)
        # except ValueError:
        #     print("No plastic strain data available!")

        
        # stress_rows = []
        # for data in zip(stress_raw[0], stress_raw[1]):
        #     stress_rows.append(pd.Series([data[0], data[1][0], data[1][1], data[1][2], data[1][3], data[1][4], data[1][5]]))
        #     self.stress = pd.DataFrame(stress_rows)
        #     self.stress.columns = ["Node", "X", "Y", "Z", "XY", "YZ", "XZ"]
        #     self.stress.set_index("Node", inplace=True)

        # elastic_strain_rows = []      
        # for data in zip(elastic_strain_raw[0], elastic_strain_raw[1]):
        #     elastic_strain_rows.append(pd.Series([data[0], data[1][0], data[1][1], data[1][2], data[1][3], data[1][4], data[1][5], data[1][6]]))
        #     self.elastic_strain = pd.DataFrame(stress_rows)
        #     self.elastic_strain.columns = ["Node", "X", "Y", "Z", "XY", "YZ", "XZ", "EQV"]
        #     self.elastic_strain.set_index("Node", inplace=True)

        # if plastic_strain_raw is not None:
        #     plastic_strain_rows = []
        #     for data in zip(plastic_strain_raw[0], plastic_strain_raw[1]):
        #         plastic_strain_rows.append(pd.Series([data[0], data[1][0], data[1][1], data[1][2], data[1][3], data[1][4], data[1][5], data[1][6]]))
        #         self.plastic_strain = pd.DataFrame(stress_rows)
        #         self.plastic_strain.columns = ["Node", "X", "Y", "Z", "XY", "YZ", "XZ", "EQV"]
        #         self.plastic_strain.set_index("Node", inplace=True)

        t0 = time.time()
        print("Making dfs")

        self.stress = pd.DataFrame.from_dict(self.stress, orient='index')
        self.elastic_strain = pd.DataFrame.from_dict(self.elastic_strain, orient='index')

        if self.plastic_strain is not None:
            self.plastic_strain = pd.DataFrame.from_dict(self.plastic_strain, orient='index')

        print(f"Making dfs: {time.time() - t0}")

        result.plot_principal_nodal_stress(i, comp="SEQV")

    def stress_dataframe(self):
        return self.stress

    def strain_dataframe(self):
        if self.plastic_strain is not None:
            return self.elastic_strain.add(self.plastic_strain)
        else:
            return self.elastic_strain

    def linearized_stress_result(self, flat=False):
        dataframe = self.stress_dataframe()
        
        top_path = _FLAT_TOP_SURFACE_PATH if flat else _TOP_SURFACE_PATH
        bot_path = _FLAT_BOTTOM_SURFACE_PATH if flat else _BOTTOM_SURFACE_PATH
        all_path = _FLAT_ALL_LOCS_PATH if flat else _ALL_LOCS_PATH

        return surface.linearize_surface(
            top_path,
            bot_path,
            dataframe,
            all_path,
            None,
            False
        )

    def linearized_strain_result(self, flat=False):
        dataframe = self.strain_dataframe()
        dataframe = dataframe.drop(dataframe.columns[6], axis=1)

        top_path = _FLAT_TOP_SURFACE_PATH if flat else _TOP_SURFACE_PATH
        bot_path = _FLAT_BOTTOM_SURFACE_PATH if flat else _BOTTOM_SURFACE_PATH
        all_path = _FLAT_ALL_LOCS_PATH if flat else _ALL_LOCS_PATH

        return surface.linearize_surface(
            top_path,
            bot_path,
            dataframe,
            all_path,
            None,
            True
        )

    def max_linearized_stresses(self, flat=False):
        lin_result = self.linearized_stress_result(flat=flat)
        return {
            'membrane': lin_result['membrane'].max(),
            'bending': lin_result['bending'].max(),
            'linearized': (lin_result['membrane'] + lin_result['bending']).max()
        }

    def max_linearized_strains(self, flat=False):
        lin_result = self.linearized_strain_result(flat=flat)
        return {
            'membrane': lin_result['membrane'].max(),
            'bending': lin_result['bending'].max(),
            'linearized': (lin_result['membrane'] + lin_result['bending']).max()
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
