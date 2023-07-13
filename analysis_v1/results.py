import os.path
import sys
import pandas as pd

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


BLACKLIST = [1, 12]
START = 0
END = 100

xy = pd.read_csv(os.path.join(PARENT_DIR, 'analysis_v1', 'in', 'base_parameters.frame'), index_col=0)
xy = xy[['heated-surf:heat_flux:wall', 'mass-flow-inlet:mass_flux:mass-flow-inlet']]
xy = xy.drop(BLACKLIST)
xy = xy.loc[START:END - 1]

solver = solve(start=START, end=END)

# nodeContext = NodeContext(r"D:\projects\diverters\src\conductivity_effect\in\kdoped_rhenium_high.inp")
# nodeContext.add_component('cool_surf1')
# nodeContext.add_component('cool_surf2')
# nodeContext.run()

# press_bound_df = pd.concat([nodeContext.result('cool_surf1'), nodeContext.result('cool_surf2')])
# press_bound_nodes = press_bound_df.index.to_numpy()
# press_bound_df.to_csv(os.path.join(PARENT_DIR, 'inp', 'nodes', 'press_bound.loc'))
press_bound_df = pd.read_csv(os.path.join(PARENT_DIR, 'inp', 'nodes', 'press_bound.loc'), index_col=0)
press_bound_nodes = press_bound_df.index.to_numpy()

ids = []
stress = {}
strain = {}

for i in range(START, END):
    if i in BLACKLIST:
        continue

    ids.append(i)
    name = f"wl10_idx{i}"
    result = solver.result_from_name(name)
    print(f"Name: {name}")

    add_lin_results(stress, result.max_linearized_stresses())
    add_lin_results(strain, result.max_linearized_strains())
    stress['eqv'] = stress.get('eqv', []) + [result.max_eqv_stress(nodes=press_bound_nodes)]
    strain['eqv'] = strain.get('eqv', []) + [result.max_eqv_strain(nodes=press_bound_nodes)]

df = pd.DataFrame(
    {
        'heat_flux': xy.iloc[:, 0].to_numpy(),
        'mass_flow_rate': xy.iloc[:, 1].to_numpy(),
        'max_eqv_stress': stress['eqv'],
        'membrane_stress': stress['membrane'],
        'bending_stress': stress['bending'],
        'linearized_stress': stress['linearized'],
        'max_eqv_strain': strain['eqv'],
        'membrane_strain': strain['membrane'],
        'bending_strain': strain['bending'],
        'linearized_strain': strain['linearized']
    },
    index=ids
)
df.to_csv(os.path.join(CURR_DIR, 'results.frame'))
print(df)
