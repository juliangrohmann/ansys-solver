import os.path
import sys
import pandas as pd
import argparse

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from analysis_v3 import solve
from analysis_util import eval_results
from apdl_util import util
from analysis_v3.configs import flat_config_plastic, curved_config_plastic

def get_name(row):
    return f"w_{row['load_id']:.0f}_" \
                      f"{row['elastic_mod_factor']:.2f}_" \
                      f"{row['yield_strength_factor']:.2f}_" \
                      f"{row['tangent_mod_factor']:.2f}"


def eval(start, end, flat, filename):
    parameters = pd.read_csv(os.path.join(CURR_DIR, f'solve_parameters{"_flat" if flat else ""}.frame'), index_col=0).iloc[start:end, :]
    solver = solve.solve(flat_config_plastic if flat else curved_config_plastic, start=start, end=end)
    eval_results.eval_results(solver, parameters, get_name, flat == 1, out=os.path.join(CURR_DIR, filename))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('start', type=int)
    parser.add_argument('end', type=int)
    parser.add_argument('flat', type=int)
    args = parser.parse_args()

    eval(args.start, args.end, args.flat, f'results_{"flat_" if args.flat else ""}{args.start}_{args.end}.frame')
