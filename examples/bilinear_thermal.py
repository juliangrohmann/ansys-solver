import os.path
import sys
import numpy as np

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample

# Initialize directories
INP_DIR = os.path.join(PARENT_DIR, 'inp')
PRESS_DIR = os.path.join(INP_DIR, 'pressure')
THERM_DIR = os.path.join(INP_DIR, 'thermal')
OUT_DIR = os.path.join(CURR_DIR, 'out')
INP_FILE = os.path.join(INP_DIR, 'hemj_v2.inp')

# Initialize sample values
elastic_mods = np.linspace(1e10, 6e10, 3)
yield_strengths = np.linspace(4.0e8, 6.5e8, 3)
tangent_mods = np.linspace(1.0e9, 2.0e9, 3)
pressure = [
    (os.path.join(PRESS_DIR, 'cool-surf1.out'), 'cool_surf1'),
    (os.path.join(PRESS_DIR, 'cool-surf2.out'), 'cool_surf2'),
    (os.path.join(PRESS_DIR, 'cool-surf3.out'), 'cool_surf3'),
    (os.path.join(PRESS_DIR, 'cool-surf4.out'), 'cool_surf4'),
    (os.path.join(PRESS_DIR, 'thimble-inner.out'), 'thimble_inner')
]
thermal = [
    (os.path.join(THERM_DIR, 'thimble.node.cfdtemp'), 'thimble_matpoint'),
    (os.path.join(THERM_DIR, 'jet.node.cfdtemp'), 'jet_matpoint')
]

# Add sample points to solver
solver = BilinearThermalSolver(INP_FILE, write_path=OUT_DIR, loglevel="INFO")
for elastic_mod in elastic_mods:
    for yield_strength in yield_strengths:
        for tangent_mod in tangent_mods:
            sample = BilinearThermalSample()
            sample.elastic_mod = elastic_mod
            sample.yield_strength = yield_strength
            sample.tangent_mod = tangent_mod

            for load in pressure:
                sample.add_pressure_load(load[0], load[1])
            for load in thermal:
                sample.add_thermal_load(load[0], load[1])

            solver.add_sample(sample)

# Solve at all sample points
solver.solve(verbose=False)
