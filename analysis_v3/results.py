import os.path
import sys
import pandas as pd

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from analysis_v3 import solve
from analysis_util import eval_results


def get_name(row):
    return f"w_{row['load_id']:.0f}_" \
                f"{row['elastic_mod_factor']:.2f}_" \
                f"{row['tangent_mod_factor']:.2f}_" \
                f"{row['yield_strength_factor']:.2f}"


START = 40
END = 100

parameters = pd.read_csv('solve_parameters.frame', index_col=0).iloc[START:END, :]
solver = solve.solve(END)
eval_results.eval_results(solver, parameters, get_name, out=os.path.join(CURR_DIR, 'results4.frame'))
