import os.path
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from parametric_solver import processing
from analysis_v3.configs import flat_config_elastic

PRESSURES = ['cool-surf1', 'cool-surf2', 'cool-surf3', 'cool-surf4', 'thimble-inner']
THERMALS = ['jet_matpoint', 'thimble_matpoint']

def process(config, blacklist=[]):
    raw_dir = os.path.join(config.INP_BASE_DIR, 'raw')
    press_out_dir = os.path.join(config.PRESS_DIR)
    therm_out_dir = os.path.join(config.THERM_DIR)

    for i in range(70, 71):
        if i in blacklist:
            continue

        print(f"Processing sample {i} ...")

        for pressure in PRESSURES:
            inp_path = os.path.join(raw_dir, 'pressure', f"{pressure}_idx{i}.out")
            out_path = os.path.join(press_out_dir, f"{pressure}_idx{i}.out")

            if not os.path.exists(press_out_dir):
                os.makedirs(press_out_dir)

            processing.process_pressure(inp_path, out_path)

        for thermal in THERMALS:
            inp_path = os.path.join(raw_dir, 'thermal', f"{thermal}_idx{i}.out")
            out_path = os.path.join(therm_out_dir, f"{thermal}_idx{i}.out")

            if not os.path.exists(therm_out_dir):
                os.makedirs(therm_out_dir)

            processing.process_temperature(inp_path, out_path)
            processing.write_temperature_load(out_path, thermal, config.FLAT)


if __name__ == '__main__':
    process(flat_config_elastic)
