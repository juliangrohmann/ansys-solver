import os
import sys
import pathlib
import numpy as np

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

import linearization.surface as surface
from apdl_util.plotting import plot_nodes
from parametric_solver.solver import NodeContext

NODES_DIR = os.path.join(PARENT_DIR, 'inp', 'nodes')
TOP_SURFACE_PATH = os.path.join(NODES_DIR, 'ts.node.loc')
BOTTOM_SURFACE_PATH = os.path.join(NODES_DIR, 'bs.node.loc')
THIMBLE_PATH = os.path.join(NODES_DIR, 'thimble_matpoint.loc')
JET_PATH = os.path.join(NODES_DIR, 'jet_matpoint.loc')
COOL_SURF4 = os.path.join(NODES_DIR, 'cool_surf4.loc')
INP_PATH = os.path.join(CURR_DIR, 'in', 'kdoped_rhenium_high.inp')

plot_nodes(INP_PATH, JET_PATH, loglevel="INFO")
# plot_nodes(INP_PATH, THIMBLE_PATH, loglevel="INFO")
