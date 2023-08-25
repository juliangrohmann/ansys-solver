import os.path
import sys
import numpy as np
import pandas as pd
import argparse
from ansys.mapdl.core.errors import MapdlExitedError

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from materials.presets import custom_structural
from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample
from parametric_solver.sampling import PropertySampler
from apdl_util import util
from analysis_v3.configs import config_util


PRESSURES = ['cool-surf1', 'cool-surf2', 'cool-surf3', 'cool-surf4', 'thimble-inner']
THERMALS = ['jet_matpoint', 'thimble_matpoint']

# WL10 Elasticity
BASE_ELASTICITY_TABLE = np.array([
    [500, 3.98e5],  # MPa
    [700, 3.9e5],
    [900, 3.68e5],
    [1100, 3.33e5],
    [1200, 3.33e5],
    [1300, 3.33e5],
    [1400, 3.33e5],
    [1500, 3.33e5],
    [1600, 3.33e5],
    [1700, 3.33e5],
    [1800, 3.33e5],
    [1900, 3.33e5],
    [2000, 3.33e5],
])
# WL10 Yield Strength
def yield_strength_poly(t):
    return 2.979e-7 * t**3 - 1.176e-3 * t**2 + 1.112 * t + 1.305e2


def generate_base_params(config):
    params_df = pd.read_csv(config.RAW_PARAMS_DIR)
    params_df = params_df[['heated-surf:heat_flux:wall', 'mass-flow-inlet:mass_flux:mass-flow-inlet']]
    params_df.rename(columns={'heated-surf:heat_flux:wall': 'heat_flux', 'mass-flow-inlet:mass_flux:mass-flow-inlet': 'mass_flow_rate'}, inplace=True)
    params_df.to_csv(config.BASE_PARAMS_DIR)


def generate_params(config, n=None):
    if n is None:
        n = 5 if config.PLASTIC else 1

    params_df = pd.read_csv(config.BASE_PARAMS_DIR, index_col=0)

    tangent_mods_df = sample_tangent_mod(len(params_df.index))

    params_df = pd.concat([params_df] * n).reset_index()
    params_df.rename(columns={'index': 'load_id'}, inplace=True)

    if config.PLASTIC:
        sampler = PropertySampler()
        sampler.add_property("yield_strength_factor", 0.50, 2.00)
        sample_df = sampler.random(len(params_df.index))
        sample_df = pd.concat([sample_df, tangent_mods_df], axis=1)
        params_df = pd.concat([params_df, sample_df], axis=1)

    params_df.to_csv(config.SOLVE_PARAMS_DIR)


def sample_tangent_mod(n):
    low_vals = np.linspace(0.01, 0.03, 6)
    high_vals = np.linspace(0.04, 0.1, 4)
    vals = np.concatenate((low_vals, high_vals))

    result = np.array([])
    for i in range(n):
        sample = np.random.choice(vals, size=4, replace=True)
        result = np.concatenate((result, sample))

    return pd.DataFrame(result, columns=['tangent_mod_factor'])


def solve(config, start=0, end=None):
    params_df = pd.read_csv(config.SOLVE_PARAMS_DIR, index_col=0)

    if end is None:
        end=params_df.shape[0]

    params_df = params_df.iloc[start:end, :]

    solver = BilinearThermalSolver(write_path=config.OUT_DIR, log_apdl=config.LOG_DIR if hasattr(config, 'LOG_DIR') else None, nproc=8)

    for index, row in params_df.iterrows():
        sample = BilinearThermalSample()
        sample.name = config.get_name(row)
        sample.input = os.path.join(config.INP_BASE_DIR, 'base.inp')
        sample.mat_ids = (2, 3) if config.FLAT else (2, 4, 6)

        print(f"Adding row {index}: {sample.name}")

        for press in PRESSURES:
            sample.add_pressure_load(os.path.join(config.PRESS_DIR, f"{press}_idx{row['load_id']:.0f}.out"), press.replace("-", "_"))
        for therm in THERMALS:
            sample.add_thermal_load(os.path.join(config.THERM_DIR, f"{therm}_idx{row['load_id']:.0f}.cdb"))

        if config.PLASTIC:
            yield_strs = np.array([yield_strength_poly(temp) for temp in BASE_ELASTICITY_TABLE[:, 0]])
            yield_strs *= row['yield_strength_factor']
            tangent_mods = BASE_ELASTICITY_TABLE[:, 1] * row['tangent_mod_factor']
            plasticity_table = np.column_stack((BASE_ELASTICITY_TABLE[:, 0], yield_strs, tangent_mods))
            print(plasticity_table)
        
        custom_structural(sample, BASE_ELASTICITY_TABLE, plasticity_table if config.PLASTIC else None)

        solver.add_sample(sample)

    solver.solve(verbose=False, kill=True)

    return solver


# if __name__ == '__main__':
#     parser = argparse.ArgumentParser()
#     parser.add_argument('shape', type=str)
#     parser.add_argument('plastic', type=str)
#     parser.add_argument('start', type=int)
#     parser.add_argument('end', type=int)
#     args = parser.parse_args()

#     solve(config_util.get_config(args.shape, args.plastic), start=args.start, end=args.end)


generate_params(config_util.get_config('flat', 'plastic'), n=4)