import os.path
import sys
import numpy as np
import pandas as pd
from ansys.mapdl.core.errors import MapdlExitedError

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from materials.presets import custom_structural
from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample
from parametric_solver.sampling import PropertySampler
from apdl_util import util

INP_BASE_DIR = os.path.join(PARENT_DIR, 'analysis_v3', 'in')
PROCESSED_DIR = os.path.join(INP_BASE_DIR, 'processed')
PRESS_DIR = os.path.join(PROCESSED_DIR, 'pressure')
THERM_DIR = os.path.join(PROCESSED_DIR, 'thermal')
OUT_DIR = os.path.join(PARENT_DIR, 'analysis_v3', 'out')

PRESSURES = ['cool-surf1', 'cool-surf2', 'cool-surf3', 'cool-surf4', 'thimble-inner']
THERMALS = ['jet_matpoint', 'thimble_matpoint']

BLACKLIST = [1, 12]

# Pure W (plastic)
BASE_ELASTICITY_TABLE = np.array([
    [500, 1.603e5],  # MPa
    [700, 1.784e5],
    [900, 1.667e5],
    [1100, 1.478e5]
])
BASE_PLASTICITY_TABLE = np.array([
    [500, 5.643e2, 1.828e1],  # MPa
    [700, 4.959e2, 4.058e1],
    [900, 4.968e2, 4.805e1],
    [1100, 4.347e2, 2.92e1]
])


def generate_params():
    params_df = pd.read_csv('base_parameters.frame', index_col=0)
    params_df = pd.concat([params_df] * 10).reset_index()
    params_df.rename(columns={'index': 'load_id'}, inplace=True)

    sampler = PropertySampler()
    sampler.add_property("elastic_mod_factor", 0.75, 1.25)
    sampler.add_property("tangent_mod_factor", 0.75, 1.25)
    sampler.add_property("yield_strength_factor", 0.75, 1.25)
    sample_df = sampler.random(len(params_df.index))
    params_df = pd.concat([params_df, sample_df], axis=1)

    params_df.to_csv('solve_parameters.frame')


def solve(n=None):
    params_df = pd.read_csv('solve_parameters.frame', index_col=0)

    if n is not None:
        params_df = params_df.iloc[0:n, :]

    solver = BilinearThermalSolver(write_path=OUT_DIR, loglevel="INFO", nproc=8)

    for index, row in params_df.iterrows():
        sample = BilinearThermalSample()
        sample.name = f"w_{row['load_id']:.0f}_" \
                      f"{row['elastic_mod_factor']:.2f}_" \
                      f"{row['tangent_mod_factor']:.2f}_" \
                      f"{row['yield_strength_factor']:.2f}"
        sample.input = os.path.join(INP_BASE_DIR, 'base.inp')

        print(f"Adding row {index}: {sample.name}")

        for press in PRESSURES:
            sample.add_pressure_load(os.path.join(PRESS_DIR, f"{press}_idx{row['load_id']:.0f}.out"), press.replace("-", "_"))
        for therm in THERMALS:
            sample.add_thermal_load(os.path.join(THERM_DIR, f"{therm}_idx{row['load_id']:.0f}.cdb"))

        elasticity_table = BASE_ELASTICITY_TABLE.copy()
        elasticity_table[:, 1] *= row['elastic_mod_factor']

        plasticity_table = BASE_PLASTICITY_TABLE.copy()
        plasticity_table[:, 1] *= row['yield_strength_factor']
        plasticity_table[:, 2] *= row['tangent_mod_factor']

        custom_structural(sample, elasticity_table, plasticity_table)

        solver.add_sample(sample)

    while True:
        try:
            solver.solve(verbose=True)
            break
        except MapdlExitedError:
            print("MAPDL Exited Error. Continuing ...")
            util.clear_mapdl()

    return solver


if __name__ == '__main__':
    # generate_params()
    solve()
