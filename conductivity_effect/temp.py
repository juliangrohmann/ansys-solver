import os.path
import sys
import numpy as np
import matplotlib.pyplot as plt
import pyvista as pv
import pandas as pd

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

import materials.presets as sampling
import conductivity_effect.solve
from materials.presets import SampleMaterial
from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample, NodeContext
from parametric_solver.util import plot_eqv_stress


NODES_DIR = os.path.join(PARENT_DIR, 'inp', 'nodes')
TOP_SURFACE_PATH = os.path.join(NODES_DIR, 'ts.node.loc')
BOTTOM_SURFACE_PATH = os.path.join(NODES_DIR, 'bs.node.loc')
ALL_LOCS_PATH = os.path.join(NODES_DIR, 'all.node.loc')

INP_DIR = os.path.join(CURR_DIR, 'in')
OUT_DIR = os.path.join(CURR_DIR, 'out')

CONDUCTIVITY = SampleMaterial.W_3RHENIUM
STRUCTURAL = SampleMaterial.W_3RHENIUM
PLASTIC = False
CASE = 'high2'


def create_result(_conductivity, _structural, _plastic, _case):
    solver = BilinearThermalSolver(write_path=OUT_DIR, loglevel="INFO", nproc=8)

    sample = BilinearThermalSample()
    sample.name = conductivity_effect.solve.sample_name(_conductivity, _structural, _plastic, _case) + '_no_temp'
    sample.input = os.path.join(INP_DIR, "base.inp")
    sampling.set_structural(sample, _structural, _plastic)
    sampling.add_pressure_loads(sample, _structural, _case)
    sampling.add_thermal_loads(sample, _structural, _case)
    solver.add_sample(sample)

    solver.solve(verbose=False)

    return solver.result_from_name(sample.name)


result = create_result(CONDUCTIVITY, STRUCTURAL, PLASTIC, CASE)
plot_eqv_stress(result)
