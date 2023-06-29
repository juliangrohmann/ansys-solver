import os.path
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from parametric_solver import processing


INP_BASE_DIR = os.path.join(PARENT_DIR, 'analysis_v1', 'in')
RAW_DIR = os.path.join(INP_BASE_DIR, 'raw')
PROCESSED_DIR = os.path.join(INP_BASE_DIR, 'processed')
PRESS_OUT_DIR = os.path.join(PROCESSED_DIR, 'pressure')
THERM_OUT_DIR = os.path.join(PROCESSED_DIR, 'thermal')

PRESSURES = ['cool-surf1', 'cool-surf2', 'cool-surf3', 'cool-surf4', 'thimble-inner']
THERMALS = ['jet_matpoint', 'thimble_matpoint']


for i in range(13, 100):
    if i == 1 or i == 12:
        continue

    print(f"Processing sample {i} ...")

    for pressure in PRESSURES:
        inp_path = os.path.join(RAW_DIR, 'pressure', f"{pressure}_idx{i}.out")
        out_path = os.path.join(PRESS_OUT_DIR, f"{pressure}_idx{i}.out")

        if not os.path.exists(PRESS_OUT_DIR):
            os.makedirs(PRESS_OUT_DIR)

        processing.process_pressure(inp_path, out_path)

    for thermal in THERMALS:
        inp_path = os.path.join(RAW_DIR, 'thermal', f"{thermal}_idx{i}.out")
        out_path = os.path.join(THERM_OUT_DIR, f"{thermal}_idx{i}.out")

        if not os.path.exists(THERM_OUT_DIR):
            os.makedirs(THERM_OUT_DIR)

        processing.process_temperature(inp_path, out_path)
        processing.write_temperature_load(out_path, thermal)
