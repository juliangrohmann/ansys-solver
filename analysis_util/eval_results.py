import os.path
import sys
import pandas as pd
import time

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from analysis_v1.solve import solve
from parametric_solver.solver import NodeContext
from linearization import linearization


def add_lin_results(dict_target, lin_result):
    dict_target['membrane'] = dict_target.get('membrane', []) + [lin_result['membrane']]
    dict_target['bending'] = dict_target.get('bending', []) + [lin_result['bending']]
    dict_target['linearized'] = dict_target.get('linearized', []) + [lin_result['linearized']]


def eval_results(solver, parameters, name_provider, out=None):
    if out is None:
        out = os.path.join(CURR_DIR, 'results.frame')

    press_bound_df = pd.read_csv(os.path.join(PARENT_DIR, 'inp', 'nodes', 'press_bound.loc'), index_col=0)
    press_bound_nodes = press_bound_df.index.to_numpy()

    stress = {}
    strain = {}

    for index, row in parameters.iterrows():
        name = name_provider(row)
        result = solver.result_from_name(name)
        print(f"Name: {name}")
        
        add_lin_results(stress, result.max_linearized_stresses())
        add_lin_results(strain, result.max_linearized_strains())
        # stress['eqv'] = stress.get('eqv', []) + [result.max_eqv_stress(nodes=press_bound_nodes)]
        # strain['eqv'] = strain.get('eqv', []) + [result.max_eqv_strain(nodes=press_bound_nodes)]

    results_df = pd.DataFrame(
        {
            'membrane_stress': stress['membrane'],
            'bending_stress': stress['bending'],
            'linearized_stress': stress['linearized'],
            'membrane_strain': strain['membrane'],
            'bending_strain': strain['bending'],
            'linearized_strain': strain['linearized']
        },
        index=parameters.index
    )
    results_df = pd.concat([parameters, results_df], axis=1)
    results_df.to_csv(out)