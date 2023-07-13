import os
import sys
import numpy as np
import enum

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from parametric_solver.solver import MatProp


class SampleMaterial(enum.Enum):
    W_3RHENIUM = 'kdoped_rhenium'
    WL10 = 'wl10_roedig'
    PURE_W = 'pure_w'


def set_structural(sample, sample_material, plastic):
    if sample_material == SampleMaterial.W_3RHENIUM:
        w_3re_structural(sample, plastic)
    elif sample_material == SampleMaterial.PURE_W:
        w_structural(sample, plastic)
    elif sample_material == SampleMaterial.WL10 and not plastic:
        wl10_structural(sample)
    else:
        print(f"Unknown structural sample material: {sample_material}, {'plastic' if plastic else 'elastic'}")


def w_3re_structural(sample, plastic):
    elastic_mod_table = np.array([
        [500, 2.266e5],  # MPa
        [700, 2.758e5],
        [900, 1.964e5],
        [1100, 1.706e5]
    ])
    plasticity_table = np.array([
        [500, 6.708e2, 2.545e1],  # MPa
        [700, 6.688e2, 5.349e1],
        [900, 5.617e2, 5.734e1],
        [1100, 5.733e2, 4.13e1]
    ])
    thermal_expansion_table = np.array([
        [20, 4.5918e-6],
        [2000, 5.994e-6],
    ])

    sample.set_property(MatProp.ELASTIC_MODULUS, elastic_mod_table)
    sample.set_property(MatProp.POISSONS_RATIO, 0.3)
    sample.set_property(MatProp.DENSITY, 1.955e-8)
    sample.set_property(MatProp.THERMAL_EXPANSION, thermal_expansion_table)
    # sample.set_property(MatProp.THERMAL_EXPANSION, 4.48e-6)

    if plastic:
        sample.plasticity = plasticity_table

    return sample


def w_structural(sample, plastic):
    elastic_mod_table = np.array([
        [500, 1.603e5],  # MPa
        [700, 1.784e5],
        [900, 1.667e5],
        [1100, 1.478e5]
    ])
    plasticity_table = np.array([
        [500, 5.643e2, 1.828e1],  # MPa
        [700, 4.959e2, 4.058e1],
        [900, 4.968e2, 4.805e1],
        [1100, 4.347e2, 2.92e1]
    ])
    thermal_expansion_table = np.array([
        [20, 4.5918e-6],
        [2000, 5.994e-6],
    ])

    sample.set_property(MatProp.ELASTIC_MODULUS, elastic_mod_table)
    sample.set_property(MatProp.POISSONS_RATIO, 0.28)
    sample.set_property(MatProp.DENSITY, 1.928e-8)
    sample.set_property(MatProp.THERMAL_EXPANSION, thermal_expansion_table)

    if plastic:
        sample.plasticity = plasticity_table

    return sample


def custom_structural(sample, elastic_mod_table, plasticity_table):
    thermal_expansion_table = np.array([
        [20, 4.5918e-6],
        [2000, 5.994e-6],
    ])

    sample.set_property(MatProp.ELASTIC_MODULUS, elastic_mod_table)
    sample.set_property(MatProp.POISSONS_RATIO, 0.28)
    sample.set_property(MatProp.DENSITY, 1.928e-8)
    sample.set_property(MatProp.THERMAL_EXPANSION, thermal_expansion_table)

    if plasticity_table is not None:
        sample.plasticity = plasticity_table

    return sample


def wl10_structural(sample):
    density_table = np.array([
        [20, 1.93e-8],
        [500, 1.92e-8],
        [1000, 1.9e-8],
        [1500, 1.89e-8]
    ])
    elastic_mod_table = np.array([
        [500, 3.98e5],  # MPa
        [700, 3.9e5],
        [900, 3.68e5],
        [1100, 3.33e5]
    ])
    thermal_expansion_table = np.array([
        [20, 4.5918e-6],
        [2000, 5.994e-6],
    ])
    poissons_table = np.array([
        [20, 0.28],
        [500, 0.28],
        [1000, 0.29],
        [1500, 0.30]
    ])

    sample.set_property(MatProp.ELASTIC_MODULUS, elastic_mod_table)
    sample.set_property(MatProp.POISSONS_RATIO, poissons_table)
    sample.set_property(MatProp.DENSITY, density_table)
    sample.set_property(MatProp.THERMAL_EXPANSION, thermal_expansion_table)

    return sample


def add_pressure_loads(sample, sample_material, case):
    pressure_dir = os.path.join(PARENT_DIR, 'inp', 'processed', sample_material.value, case, 'pressure')

    sample.add_pressure_load(os.path.join(pressure_dir, 'cool-surf1.out'), 'cool_surf1')
    sample.add_pressure_load(os.path.join(pressure_dir, 'cool-surf2.out'), 'cool_surf2')
    sample.add_pressure_load(os.path.join(pressure_dir, 'cool-surf3.out'), 'cool_surf3')
    sample.add_pressure_load(os.path.join(pressure_dir, 'cool-surf4.out'), 'cool_surf4')
    sample.add_pressure_load(os.path.join(pressure_dir, 'thimble-inner.out'), 'thimble_inner')


def add_thermal_loads(sample, sample_material, case):
    thermal_dir = os.path.join(PARENT_DIR, 'inp', 'processed', sample_material.value, case, 'thermal')

    sample.add_thermal_load(os.path.join(thermal_dir, 'thimble_matpoint.cdb'), 'thimble_matpoint')
    sample.add_thermal_load(os.path.join(thermal_dir, 'jet_matpoint.cdb'), 'jet_matpoint')

