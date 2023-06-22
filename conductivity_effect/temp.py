import os.path
import sys
import numpy as np
import matplotlib.pyplot as plt
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

name = conductivity_effect.solve.sample_name(SampleMaterial.WL10, SampleMaterial.PURE_W, False, 'high')
solver = conductivity_effect.solve.solve(names=[name])
result = solver.result_from_name(name)

strain_df = result.strain_dataframe()

loc1, loc2 = surface.pair_nodes(
    None,
    TOP_SURFACE_PATH,
    BOTTOM_SURFACE_PATH
)

locs = pd.concat([loc1, loc2])

indeces = np.intersect1d(locs.index.to_numpy(), strain_df.index.to_numpy())

strain_df = strain_df.loc[indeces]
locs = locs.loc[indeces]

strain_vals = von_mises_strain(strain_df.to_numpy())
# strain_vals = strain_df.iloc[:, 6].to_numpy()
pd.set_option('display.max_columns', 500)
print(strain_df)
print(strain_vals)
loc_vals = locs.loc[strain_df.index.to_numpy()].to_numpy()

point_cloud = pv.PolyData(loc_vals)
point_cloud["strain"] = strain_vals

plotter = pv.Plotter()
plotter.add_mesh(point_cloud, cmap='turbo', point_size=12)
plotter.view_vector((10, 10, 10), (0, 0, 0))
plotter.camera.roll = 240
plotter.add_title("Strain")
plotter.render()
plotter.show()
