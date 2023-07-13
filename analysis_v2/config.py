import os.path
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from parametric_solver import processing
from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample
from materials import presets


_IN_DIR = os.path.join(CURR_DIR, 'in')
_NODES_DIR = os.path.join(PARENT_DIR, 'inp', 'nodes')

RAW_DIR = os.path.join(_IN_DIR, 'raw', 'wl10_roedig')
PROCESSED_DIR = os.path.join(_IN_DIR, 'processed', 'wl10_roedig')
INP_BASE_FILE = os.path.join(_IN_DIR, 'base.inp')
OUT_DIR = os.path.join(PARENT_DIR, 'analysis_v2', 'out')

TOP_SURFACE_PATH = os.path.join(_NODES_DIR, 'ts.node.loc')
BOTTOM_SURFACE_PATH = os.path.join(_NODES_DIR, 'bs.node.loc')
ALL_LOCS_PATH = os.path.join(_NODES_DIR, 'all.node.loc')

PRESSURES = ['cool-surf1', 'cool-surf2', 'cool-surf3', 'cool-surf4', 'thimble-inner']
THERMALS = ['jet_matpoint', 'thimble_matpoint']
CASES = ['low', 'nominal', 'high']