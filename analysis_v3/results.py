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


def get_name(row):
    return f"w_{row['load_id']:.0f}_" \
                      f"{row['elastic_mod_factor']:.2f}_" \
                      f"{row['yield_strength_factor']:.2f}_" \
                      f"{row['tangent_mod_factor']:.2f}"


def eval(start, end, filename):
    parameters = pd.read_csv(os.path.join(CURR_DIR, 'solve_parameters.frame'), index_col=0).iloc[start:end, :]
    solver = solve.solve(start=start, end=end)
    eval_results.eval_results(solver, parameters, get_name, out=os.path.join(CURR_DIR, filename))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('start', type=int)
    parser.add_argument('end', type=int)
    args = parser.parse_args()

    eval(args.start, args.end, f'results_{args.start}_{args.end}.frame')
