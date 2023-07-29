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
from analysis_v3.configs import config_util 


def eval(start, end, config):
    parameters = pd.read_csv(config.SOLVE_PARAMS_DIR, index_col=0).iloc[start:end, :]
    solver = solve.solve(config, start=start, end=end)
    eval_results.eval_results(solver, parameters, config.get_name, config.FLAT, out=config.RESULTS_DIR)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('start', type=int)
    parser.add_argument('end', type=int)
    parser.add_argument('shape', type=str)
    parser.add_argument('plastic', type=str)
    args = parser.parse_args()

    eval(args.start, args.end, config_util.get_config(args.shape, args.plastic))
