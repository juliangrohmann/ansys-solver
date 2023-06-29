import os.path
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import LinearNDInterpolator

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from analysis_v1.solve import solve
from parametric_solver.solver import NodeContext


BLACKLIST = [1, 12]
START = 0
END = 85

xy = pd.read_csv(os.path.join(PARENT_DIR, 'analysis_v1', 'in', 'parameters.frame'), index_col=0)
xy = xy[['heated-surf:heat_flux:wall', 'mass-flow-inlet:mass_flux:mass-flow-inlet']]
xy = xy.drop(BLACKLIST)
xy = xy.loc[START:END - 1]
print(xy)

solver = solve(start=START, end=END)

nodeContext = NodeContext(r"D:\projects\diverters\src\conductivity_effect\in\kdoped_rhenium_high.inp")
nodeContext.add_component('cool_surf1')
nodeContext.add_component('cool_surf2')
nodeContext.run()

press_bound_df = pd.concat([nodeContext.result('cool_surf1'), (nodeContext.result('cool_surf2'))])
press_bound_nodes = press_bound_df.index.to_numpy()

max_eqv_stress = []
for i in range(START, END):
    if i in BLACKLIST:
        continue

    name = f"wl10_idx{i}"
    result = solver.result_from_name(name)
    max_eqv_stress.append(max([result.eqv_stress(node) for node in press_bound_nodes]))

x = xy.iloc[:, 0].to_numpy()
y = xy.iloc[:, 1].to_numpy()
z = np.array(max_eqv_stress)

X = np.linspace(min(x), max(x))
Y = np.linspace(min(y), max(y))

X, Y = np.meshgrid(X, Y)
interp = LinearNDInterpolator(list(zip(x, y)), z)
Z = interp(X, Y)

df = pd.DataFrame({'heat_flux': X, 'mass_flow_rate': y, 'max_eqv_stress': z})
df.to_csv(os.path.join(CURR_DIR, 'lin_interp.frame'))

# plt.pcolormesh(X, Y, Z, shading='auto')
# plt.plot(x, y, "ok", label="Solution result")
# plt.legend()
# plt.colorbar()
# plt.xlabel("Heat Flux (W/m^2)")
# plt.ylabel("Mass Flow Rate (g/s)")
# plt.show()
#
# fig = plt.figure()
# ax = fig.add_subplot(projection='3d')
# ax.set_xlabel("Heat Flux (W/m^2)")
# ax.set_ylabel("Mass Flow Rate (g/s)")
# ax.set_zlabel("Max. Eqv. Stress (MPa)", labelpad=-2)
# ax.scatter(X, Y, Z)
# plt.show()
