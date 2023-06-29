import os.path
import sys
import numpy as np
import pyvista as pv
import pandas as pd

PARENT_DIR = r'D:\projects\diverters\src'
CURR_DIR = os.path.join(PARENT_DIR, 'conductivity_effect')
sys.path.append(PARENT_DIR)

import materials.presets as sampling
import linearization.surface as surface
import conductivity_effect.solve
from linearization.linearization import von_mises, von_mises_strain
from materials.presets import SampleMaterial
from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample, NodeContext


NODES_DIR = os.path.join(PARENT_DIR, 'inp', 'nodes')
TOP_SURFACE_PATH = os.path.join(NODES_DIR, 'ts.node.loc')
BOTTOM_SURFACE_PATH = os.path.join(NODES_DIR, 'bs.node.loc')
ALL_LOCS_PATH = os.path.join(NODES_DIR, 'all.node.loc')

INP_DIR = os.path.join(CURR_DIR, 'in')
OUT_DIR = os.path.join(CURR_DIR, 'out')


def plot_eqv_stress(result):
    _plot_df_prop(result.stress_dataframe())


def plot_eqv_strain(result):
    _plot_df_prop(result.strain_dataframe())


def _plot_df_prop(df_vals):
    loc1, loc2 = surface.pair_nodes(
        None,
        TOP_SURFACE_PATH,
        BOTTOM_SURFACE_PATH
    )

    locs = pd.concat([loc1, loc2])

    indeces = np.intersect1d(locs.index.to_numpy(), df_vals.index.to_numpy())

    df_vals = df_vals.loc[indeces]
    locs = locs.loc[indeces]

    stress_vals = von_mises(df_vals.to_numpy())
    pd.set_option('display.max_columns', 500)
    loc_vals = locs.loc[df_vals.index.to_numpy()].to_numpy()

    point_cloud = pv.PolyData(loc_vals)
    point_cloud["stress"] = stress_vals

    plotter = pv.Plotter()
    plotter.add_mesh(point_cloud, cmap='turbo', point_size=12)
    plotter.view_vector((10, 10, 10), (0, 0, 0))
    plotter.camera.roll = 240
    plotter.add_title("Stress")
    plotter.render()
    plotter.show()
