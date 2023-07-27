import os
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)


INP_BASE_DIR = os.path.join(PARENT_DIR, 'in')
PROCESSED_DIR = os.path.join(INP_BASE_DIR, 'processed')
PRESS_DIR = os.path.join(PROCESSED_DIR, 'pressure')
THERM_DIR = os.path.join(PROCESSED_DIR, 'thermal')

RAW_PARAMS_DIR = os.path.join(INP_BASE_DIR, 'parameters.frame')
BASE_PARAMS_DIR = os.path.join(CURR_DIR, 'base_parameters.frame')

OUT_DIR = os.path.join(PARENT_DIR, 'analysis_v3', 'out')
SOLVE_PARAMS_DIR = os.path.join(CURR_DIR, 'solve_parameters.frame')

FLAT = False
PLASTIC = True
IS_ELASTIC_PARAM = False
