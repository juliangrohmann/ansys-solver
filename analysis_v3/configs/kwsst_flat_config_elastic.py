import os
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)


INP_BASE_DIR = os.path.join(PARENT_DIR, 'in_kwsst_flat')
PROCESSED_DIR = os.path.join(INP_BASE_DIR, 'processed')
PRESS_DIR = os.path.join(PROCESSED_DIR, 'pressure')
THERM_DIR = os.path.join(PROCESSED_DIR, 'thermal')

RAW_PARAMS_DIR = os.path.join(INP_BASE_DIR, 'parameters.frame')
BASE_PARAMS_DIR = os.path.join(PARENT_DIR, 'params', 'base_params_kwsst_flat.frame')

OUT_DIR = os.path.join(PARENT_DIR, 'out_kwsst_flat_elastic')
SOLVE_PARAMS_DIR = os.path.join(PARENT_DIR, 'params', 'solve_params_kwsst_flat_elastic.frame')
RESULTS_DIR = os.path.join(PARENT_DIR, 'results', 'result_kwsst_flat_elastic.frame')

FLAT = True
PLASTIC = False


def get_name(row):
    return f"wl10_{row['load_id']:.0f}"
