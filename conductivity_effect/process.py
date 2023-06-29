import os.path
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from parametric_solver import processing
from materials.presets import SampleMaterial


INP_BASE_DIR = os.path.join(PARENT_DIR, 'inp', 'raw')
OUT_BASE_DIR = os.path.join(PARENT_DIR, 'inp', 'processed')

# MATERIALS = [SampleMaterial.W_3RHENIUM, SampleMaterial.WL10]
MATERIALS = [SampleMaterial.W_3RHENIUM]
# CASES = ['low', 'nominal', 'high', 'high2']
CASES = ['high2']
PRESSURES = ['cool-surf1', 'cool-surf2', 'cool-surf3', 'cool-surf4', 'thimble-inner']
THERMALS = ['jet_matpoint', 'thimble_matpoint']

for mat in MATERIALS:
    for case in CASES:
        for pressure in PRESSURES:
            inp_path = os.path.join(INP_BASE_DIR, mat.value, case, 'pressure')
            out_path = os.path.join(OUT_BASE_DIR, mat.value, case, 'pressure')

            if not os.path.exists(out_path):
                os.makedirs(out_path)

            processing.process_pressure(inp_path, out_path, pressure)

        for thermal in THERMALS:
            inp_path = os.path.join(INP_BASE_DIR, mat.value, case, 'thermal')
            out_path = os.path.join(OUT_BASE_DIR, mat.value, case, 'thermal')

            if not os.path.exists(out_path):
                os.makedirs(out_path)

            processing.process_temperature(inp_path, out_path, thermal)

processing.write_temperature_load(r'D:\projects\diverters\src\inp\processed\kdoped_rhenium\high2\thermal', 'thimble_matpoint')
processing.write_temperature_load(r'D:\projects\diverters\src\inp\processed\kdoped_rhenium\high2\thermal', 'jet_matpoint')
