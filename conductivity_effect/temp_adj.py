import os
import sys
import pandas as pd
import numpy as np

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

K_DOPED_RE = r'C:\Users\PC\Downloads\conductivity_effect\conductivity_effect\kdoped_rhenium'
OUT_DIR = os.path.join(PARENT_DIR, 'conductivity_effect', 'in', 'temp_interp', 'kdoped_rhenium', 'matpoint')

CASES = ['low', 'nominal', 'high']
COMPS = ['jet_matpoint.out', 'thimble_matpoint.out']
MIDPOINTS = 3


def read_df(_comp, _case):
    _path = os.path.join(K_DOPED_RE, _case, _comp)
    _df = pd.read_csv(_path, index_col=0)
    _df.columns = _df.columns.str.strip()
    return _df


def write_offset(_comp, _case, _dt, _i):
    _df = read_df(_comp, _case)
    _df['temperature'] = _df['temperature'] + _dt * _i
    print(f"{_comp}, {_case}: {_df['temperature'].mean()}")
    _path = os.path.join(OUT_DIR, f'{comp[:-4]}_{_case}_{i}.out')
    _df.to_csv(_path)


ref_t = {}

for case in CASES:
    for comp in COMPS:
        df = read_df(comp, case)
        mean_t = df['temperature'].mean()

        if comp not in ref_t:
            ref_t[comp] = []

        ref_t[comp].append(mean_t)

for comp in COMPS:
    low_dt = (ref_t[comp][1] - ref_t[comp][0]) / (MIDPOINTS + 1)
    high_dt = (ref_t[comp][2] - ref_t[comp][1]) / (MIDPOINTS + 1)

    for i in range(1, MIDPOINTS + 1):
        write_offset(comp, CASES[0], low_dt, i)
        write_offset(comp, CASES[1], high_dt, i)
