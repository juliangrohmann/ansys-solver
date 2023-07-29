import os
import sys

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)


INP_BASE_DIR = os.path.join(PARENT_DIR, 'in_curved')
PROCESSED_DIR = os.path.join(INP_BASE_DIR, 'processed')
PRESS_DIR = os.path.join(PROCESSED_DIR, 'pressure')
THERM_DIR = os.path.join(PROCESSED_DIR, 'thermal')

RAW_PARAMS_DIR = os.path.join(INP_BASE_DIR, 'parameters.frame')
BASE_PARAMS_DIR = os.path.join(PARENT_DIR, 'params', 'base_params_curved.frame')

OUT_DIR = os.path.join(PARENT_DIR, 'out_curved_plastic')
SOLVE_PARAMS_DIR = os.path.join(PARENT_DIR, 'params', 'solve_params_curved_plastic.frame')
RESULTS_DIR = os.path.join(PARENT_DIR, 'results', 'result_curved_plastic.frame')

FLAT = False
PLASTIC = True


def get_name(row):
    return f"wl10_{row['load_id']:.0f}_" \
                      f"{row['yield_strength_factor']:.2f}_" \
                      f"{row['tangent_mod_factor']:.2f}"
