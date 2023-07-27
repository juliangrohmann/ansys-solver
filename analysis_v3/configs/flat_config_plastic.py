import os
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)


INP_BASE_DIR = os.path.join(PARENT_DIR, 'in_flat')
PROCESSED_DIR = os.path.join(INP_BASE_DIR, 'processed')
PRESS_DIR = os.path.join(PROCESSED_DIR, 'pressure')
THERM_DIR = os.path.join(PROCESSED_DIR, 'thermal')

RAW_PARAMS_DIR = os.path.join(INP_BASE_DIR, 'parameters.frame')
BASE_PARAMS_DIR = os.path.join(PARENT_DIR, 'base_parameters_flat.frame')

OUT_DIR = os.path.join(PARENT_DIR, 'out_flat')
SOLVE_PARAMS_DIR = os.path.join(PARENT_DIR, 'solve_parameters_flat.frame')

FLAT = True
PLASTIC = True
IS_ELASTIC_PARAM = False