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
INP_PATH = os.path.join(CURR_DIR, 'in', 'kdoped_rhenium_high.inp')

# plot_nodes(INP_PATH, BOTTOM_SURFACE_PATH, loglevel="INFO")

context = NodeContext(INP_PATH)
context.add_component("all", inactive=True, mid=True)
context.run()
context.write("all", "all.node.loc", mult=0.001)
