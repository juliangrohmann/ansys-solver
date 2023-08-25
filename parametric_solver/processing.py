import os
import sys
import pandas as pd
from scipy.interpolate import NearestNDInterpolator, LinearNDInterpolator

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from parametric_solver.solver import NodeContext

ELEMENT_ROOT = os.path.join(PARENT_DIR, 'inp', 'processing')
NODE_DIR = os.path.join(PARENT_DIR, 'inp', 'nodes')


def process_pressure(in_path, out_path):
    df = pd.read_csv(in_path, index_col=0)
    df.columns = df.columns.str.strip()
    df.loc[:, 'total-pressure'] /= 1e6
    df.iloc[:, 0:3] *= 1000
    df.to_csv(out_path)


def process_temperature(in_path, out_path):
    df = pd.read_csv(in_path, index_col=0)
    df.columns = df.columns.str.strip()
    df.iloc[:, 0:3] *= 1000
    df.iloc[:, 3] -= 273.15
    df.to_csv(out_path)


def write_temperature_load(load_path, component, flat):
    raw_data = pd.read_csv(load_path, index_col=0)
    raw_locs = raw_data.iloc[:, 0:3]
    raw_temps = raw_data.iloc[:, 3]

    target_nodes = os.path.join(NODE_DIR, f"flat_{component}.loc" if flat else f"{component}.loc")
    target_data = pd.read_csv(target_nodes, index_col=0)
    target_locs = target_data.iloc[:, 0:3]

    lin_interp = NearestNDInterpolator(raw_locs, raw_temps)
    target_data['temperature'] = lin_interp(target_locs)
    load_str = f"bfblock,2,temp,{target_data.index.max()},{target_data.shape[0]},0\n(i9,e20.9e3)\n"

    for i in range(target_data.shape[0]):
        load_str += "{: >9} {: >19.9e}\n".format(target_data.index[i], target_data['temperature'].iloc[i])
    load_str += "bf,end,loc,-1,\n"

    load_dir = os.path.dirname(load_path)
    filename = os.path.basename(load_path)
    real_name = os.path.splitext(filename)[0]

    with open(os.path.join(load_dir, real_name + '.cdb'), 'w') as f:
        f.write(load_str)
