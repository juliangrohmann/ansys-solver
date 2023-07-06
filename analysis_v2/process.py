import os.path
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from parametric_solver import processing
from analysis_v2 import config


for case in config.CASES:
    print(f"Processing {case} ...")

    for pressure in config.PRESSURES:
        inp_path = os.path.join(config.RAW_DIR, case, 'pressure', f"{pressure}.out")
        out_path = os.path.join(config.PROCESSED_DIR, case, 'pressure', f"{pressure}.out")

        processing.process_pressure(inp_path, out_path)

    for thermal in config.THERMALS:
        inp_path = os.path.join(config.RAW_DIR, case, 'thermal', f"{thermal}.out")
        out_path = os.path.join(config.PROCESSED_DIR, case, 'thermal', f"{thermal}.out")

        processing.process_temperature(inp_path, out_path)
        processing.write_temperature_load(out_path, thermal)
