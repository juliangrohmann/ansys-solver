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
BASE_PARAMS_DIR = os.path.join(CURR_DIR, 'base_parameters.frame')
SOLVE_PARAMS_DIR = os.path.join(CURR_DIR, 'solve_parameters.frame')

PRESSURES = ['cool-surf1', 'cool-surf2', 'cool-surf3', 'cool-surf4', 'thimble-inner']
THERMALS = ['jet_matpoint', 'thimble_matpoint']

BLACKLIST = [1, 12]

# WL10 Elasticity
BASE_ELASTICITY_TABLE = np.array([
    [500, 3.98e5],  # MPa
    [700, 3.9e5],
    [900, 3.68e5],
    [1100, 3.33e5]
])
# Pure W Yield Strength
BASE_PLASTICITY_TABLE = np.array([
    [500, 5.643e2, -1],  # MPa
    [700, 4.959e2, -1],
    [900, 4.968e2, -1],
    [1100, 4.347e2, -1]
])


def generate_params():
    params_df = pd.read_csv(BASE_PARAMS_DIR, index_col=0)
    params_df = pd.concat([params_df] * 20).reset_index()
    params_df.rename(columns={'index': 'load_id'}, inplace=True)

    sampler = PropertySampler()
    sampler.add_property("elastic_mod_factor", 0.70, 1.30)
    sampler.add_property("yield_strength_factor", 0.70, 1.30)
    sampler.add_property("tangent_mod_factor", 0.05, 0.40)
    sample_df = sampler.random(len(params_df.index))
    params_df = pd.concat([params_df, sample_df], axis=1)

    params_df.to_csv(SOLVE_PARAMS_DIR)


def solve(start=0, end=None):
    params_df = pd.read_csv(SOLVE_PARAMS_DIR, index_col=0)

    if end is None:
        end=params_df.shape[0]

    params_df = params_df.iloc[start:end, :]

    solver = BilinearThermalSolver(write_path=OUT_DIR, nproc=8)

    for index, row in params_df.iterrows():
        sample = BilinearThermalSample()
        sample.name = f"w_{row['load_id']:.0f}_" \
                      f"{row['elastic_mod_factor']:.2f}_" \
                      f"{row['yield_strength_factor']:.2f}_" \
                      f"{row['tangent_mod_factor']:.2f}"
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
        plasticity_table[:, 2] = BASE_ELASTICITY_TABLE[:, 1] * row['tangent_mod_factor']
        
        custom_structural(sample, elasticity_table, plasticity_table)

        solver.add_sample(sample)

    solver.solve(verbose=False, kill=True)

    return solver


if __name__ == '__main__':
    # generate_params()
    solve()
