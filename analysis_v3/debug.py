import os.path
import sys
import pandas as pd

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURR_DIR)
sys.path.append(PARENT_DIR)

from parametric_solver.solver import NodeContext, BilinearThermalSolver, BilinearThermalSample
from parametric_solver.util import plot_eqv_stress, plot_eqv_strain, plot_temperature


NODE_DIR = os.path.join(PARENT_DIR, 'inp', 'nodes')
OUT_DIR = os.path.join(CURR_DIR, 'out_kwsst_curved_elastic')

# context = NodeContext(os.path.join(CURR_DIR, 'in_flat', 'base_v2.inp'))
# context.add_component('thimble_matpoint')
# context.add_component('jet_matpoint')
# context.add_component('bot_surf')
# context.add_component('top_surf')
# context.add_component('all')
# context.run()
# context.write('thimble_matpoint', os.path.join(OUT_DIR, 'flat_thimble_matpoint.loc'))
# context.write('jet_matpoint', os.path.join(OUT_DIR, 'flat_jet_matpoint.loc'))
# context.write('bot_surf', os.path.join(OUT_DIR, 'bs_flat.node.loc'))
# context.write('top_surf', os.path.join(OUT_DIR, 'ts_flat.node.loc'))
# context.write('all', os.path.join(OUT_DIR, 'all_flat.node.loc'))

solver = BilinearThermalSolver(write_path=OUT_DIR, loglevel="INFO", nproc=8)

sample = BilinearThermalSample()
sample.name = "wl10_70"
solver.add_sample(sample)
solver.solve(verbose=True)

result = solver.result_from_name(sample.name)
plot_eqv_stress(result, False)

# df = pd.read_csv(os.path.join(CURR_DIR, 'in_curved', 'processed', 'thermal', 'thimble_matpoint_idx70.out'), index_col=0)
# plot_temperature(df, 'thimble_matpoint', False)
