import os.path
import sys
import numpy as np
import pandas as pd

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample
from analysis_v2 import config
from materials.presets import MatProp
from linearization import linearization


YIELD_STR_PRINCIPLE = [
    [565, 620, 330],  # MPa
    [494, 544, 490],
    [484, 504, 421],
    [52, 50, 60],
    [58, 58, 58],
    [32, 32, 32],
    [32, 32, 32]
]
YIELD_MODE = ['exp', 'mean', 'vm_crit', 'hill']
mode = 'exp'


def solve_fixed():
    solver = BilinearThermalSolver(write_path=config.OUT_DIR, loglevel="INFO", nproc=8)

    for case in config.CASES:
        for frac in np.linspace(0.05, 0.50, 10):
            percent = int(round(frac * 100))
            print(f"Adding sample: {case}, {percent} ...")

            sample = BilinearThermalSample()
            sample.name = f"{case}_{percent}_{mode}"
            sample.input = config.INP_BASE_FILE
            set_structural(sample, frac, mode)

            for press in config.PRESSURES:
                pressure_file = os.path.join(config.PROCESSED_DIR, case, 'pressure', f"{press}.out")
                sample.add_pressure_load(pressure_file, press.replace("-", "_"))
            for therm in config.THERMALS:
                thermal_file = os.path.join(config.PROCESSED_DIR, case, 'thermal', f"{therm}.cdb")
                sample.add_thermal_load(thermal_file)

            solver.add_sample(sample)

    solver.solve(verbose=True)
    return solver


def set_structural(sample, plast_factor, yield_mode):
    elastic_mod_table = np.array([
        [500, 3.913e5],  # MPa
        [700, 3.827e5],
        [900, 3.734e5],
        [1300, 3.528e5],
        [1500, 3.415e5],
        [1800, 3.232e5],
        [2500, 2.744e5]
    ])

    thermal_expansion_table = np.array([
        [20, 4.5918e-6],
        [2000, 5.994e-6],
    ])

    sample.set_property(MatProp.ELASTIC_MODULUS, elastic_mod_table)
    sample.set_property(MatProp.POISSONS_RATIO, 0.28)
    sample.set_property(MatProp.DENSITY, 1.928e-8)
    sample.set_property(MatProp.THERMAL_EXPANSION, thermal_expansion_table)

    if yield_mode == 'exp' or yield_mode == 'hill':
        yield_strs = experimental_yield()
        plasticity_table = np.column_stack((elastic_mod_table[:, 0], yield_strs, elastic_mod_table[:, 1] * plast_factor))
        sample.plasticity = plasticity_table

    if yield_mode == 'hill':
        hill_table = hill_yield_criterion()
        sample.hill = hill_table

    return sample


def experimental_yield():
    return [5.643e2, 4.959e2, 4.968e2, 4.347e2, 4.347e2, 4.347e2, 4.347e2]


def full_yield_tensor():
    yield_str_df = pd.DataFrame(YIELD_STR_PRINCIPLE, columns=['x', 'y', 'z'])

    yield_str_df['xy'] = (yield_str_df['x'] + yield_str_df['y']) / (2 * 3 ** 0.5)
    yield_str_df['yz'] = (yield_str_df['y'] + yield_str_df['z']) / (2 * 3 ** 0.5)
    yield_str_df['xz'] = (yield_str_df['x'] + yield_str_df['z']) / (2 * 3 ** 0.5)

    return yield_str_df


def von_mises_yield_crit():
    yield_str_df = full_yield_tensor()
    return linearization.von_mises(yield_str_df.to_numpy())


def hill_yield_criterion():
    yield_str_df = full_yield_tensor()

    temps = np.array([500, 700, 900, 1300, 1500, 1800, 2500])
    yield_iso = von_mises_yield_crit()
    c_x = (yield_str_df['x'] / yield_iso).to_numpy()
    c_y = (yield_str_df['y'] / yield_iso).to_numpy()
    c_z = (yield_str_df['z'] / yield_iso).to_numpy()
    c_xy = (yield_str_df['xy'] * 3 ** 0.5 / yield_iso).to_numpy()
    c_yz = (yield_str_df['yz'] * 3 ** 0.5 / yield_iso).to_numpy()
    c_xz = (yield_str_df['xz'] * 3 ** 0.5 / yield_iso).to_numpy()

    return np.column_stack((temps, c_z, c_y, c_x, c_yz, c_xy, c_xz))


def mean_yield():
    yield_str_df = pd.DataFrame(YIELD_STR_PRINCIPLE, columns=['x', 'y', 'z'])
    yield_strs = (yield_str_df['x'] + yield_str_df['y'] + yield_str_df['z']) / 3
    return yield_strs.to_numpy()


if __name__ == '__main__':
    solve_fixed()
