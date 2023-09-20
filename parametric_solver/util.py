import os.path
import sys
import numpy as np
import pyvista as pv
import pandas as pd
from scipy.interpolate import NearestNDInterpolator

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

import materials.presets as sampling
import linearization.surface as surface
import conductivity_effect.solve
from linearization.linearization import von_mises, von_mises_strain
from materials.presets import SampleMaterial
from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample, NodeContext


NODES_DIR = os.path.join(PARENT_DIR, 'inp', 'nodes')

CURVED_TOP_SURFACE_PATH = os.path.join(NODES_DIR, 'ts.node.loc')
CURVED_BOTTOM_SURFACE_PATH = os.path.join(NODES_DIR, 'bs.node.loc')
CURVED_ALL_LOCS_PATH = os.path.join(NODES_DIR, 'all.node.loc')

FLAT_TOP_SURFACE_PATH = os.path.join(NODES_DIR, 'ts_flat.node.loc')
FLAT_BOTTOM_SURFACE_PATH = os.path.join(NODES_DIR, 'bs_flat.node.loc')
FLAT_ALL_LOCS_PATH = os.path.join(NODES_DIR, 'all_flat.node.loc')

INP_DIR = os.path.join(CURR_DIR, 'in')
OUT_DIR = os.path.join(CURR_DIR, 'out')


def plot_eqv_stress(result, flat, col=None):
    _plot_df_prop(result.stress_dataframe(), flat, col=col)


def plot_eqv_strain(result, flat, col=None):
    _plot_df_prop(result.strain_dataframe(), flat, col=col)

def plot_temperature(df, component, flat):
    raw_locs = df.iloc[:, 0:3]
    raw_temps = df.iloc[:, 3]

    target_path = os.path.join(NODES_DIR, f'flat_{component}.loc' if flat else f"{component}.loc")
    target_data = pd.read_csv(target_path, index_col=0)
    target_locs = target_data.iloc[:, 0:3]

    lin_interp = NearestNDInterpolator(raw_locs, raw_temps)
    target_data['temperature'] = lin_interp(target_locs)
    target_data.drop(target_data.columns[[0, 1, 2]], axis=1, inplace=True)
    print(target_data)
    _plot_df_prop(target_data, flat, col='temperature')

def _plot_df_prop(df_vals, flat, col=None):
    df_vals = df_vals.dropna()
    
    loc1, loc2 = surface.pair_nodes(
        None,
        CURVED_TOP_SURFACE_PATH if not flat else FLAT_TOP_SURFACE_PATH,
        CURVED_BOTTOM_SURFACE_PATH if not flat else FLAT_BOTTOM_SURFACE_PATH
    )

    locs = pd.concat([loc1, loc2])

    indeces = np.intersect1d(locs.index.to_numpy(), df_vals.index.to_numpy())

    df_vals = df_vals.loc[indeces]
    locs = locs.loc[indeces]

    if col is None:
        stress_vals = von_mises(df_vals.to_numpy())
    else:
        stress_vals = df_vals[col].to_numpy()

    pd.set_option('display.max_columns', 500)
    loc_vals = locs.loc[df_vals.index.to_numpy()].to_numpy()

    point_cloud = pv.PolyData(loc_vals)
    point_cloud["property"] = stress_vals

    plotter = pv.Plotter()
    plotter.add_mesh(point_cloud, cmap='turbo', point_size=12)
    plotter.view_vector((10, 10, 10), (0, 0, 0))
    plotter.camera.roll = 240
    plotter.add_title("Property Plot")
    plotter.render()
    plotter.show()
