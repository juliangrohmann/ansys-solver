import os.path
import sys
from ansys.mapdl.core.errors import MapdlExitedError

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from parametric_solver import processing
from parametric_solver.solver import BilinearThermalSolver, BilinearThermalSample
from materials import presets


INP_BASE_DIR = os.path.join(PARENT_DIR, 'analysis_v1', 'in')
PROCESSED_DIR = os.path.join(INP_BASE_DIR, 'processed')
PRESS_DIR = os.path.join(PROCESSED_DIR, 'pressure')
THERM_DIR = os.path.join(PROCESSED_DIR, 'thermal')
OUT_DIR = os.path.join(PARENT_DIR, 'analysis_v1', 'out')

PRESSURES = ['cool-surf1', 'cool-surf2', 'cool-surf3', 'cool-surf4', 'thimble-inner']
THERMALS = ['jet_matpoint', 'thimble_matpoint']

BLACKLIST = [1, 12]


def solve(start=0, end=100):
    solver = BilinearThermalSolver(write_path=OUT_DIR, loglevel="INFO", nproc=8)

    for i in range(start, end):
        if i in BLACKLIST:
            continue

        print(f"Adding sample {i} ...")

        sample = BilinearThermalSample()
        sample.name = f"wl10_idx{i}"
        sample.input = os.path.join(INP_BASE_DIR, 'base.inp')
        presets.set_structural(sample, presets.SampleMaterial.WL10, False)

        for press in PRESSURES:
            sample.add_pressure_load(os.path.join(PRESS_DIR, f"{press}_idx{i}.out"), press.replace("-", "_"))
        for therm in THERMALS:
            sample.add_thermal_load(os.path.join(THERM_DIR, f"{therm}_idx{i}.cdb"))

        solver.add_sample(sample)

    while True:
        try:
            solver.solve(verbose=True)
            break
        except MapdlExitedError:
            print("MAPDL Exited Error. Continuing ...")

    return solver


if __name__ == '__main__':
    solve()

