import os.path
import sys
import pandas as pd

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(os.path.dirname(CURR_DIR))
sys.path.append(PARENT_DIR)

from parametric_solver.solver import NodeContext
from apdl_util import util


BASE_CURVED_PATH = os.path.join(CURR_DIR, 'curved.inp')
BASE_FLAT_PATH = os.path.join(CURR_DIR, 'flat.inp')

OUT_CURVED_TOP_PATH = os.path.join(CURR_DIR, 'curved_top.loc')
OUT_CURVED_BOT_PATH = os.path.join(CURR_DIR, 'curved_bot.loc')
OUT_CURVED_ALL_PATH = os.path.join(CURR_DIR, 'curved_all.loc')

OUT_FLAT_TOP_PATH = os.path.join(CURR_DIR, 'flat_top.loc')
OUT_FLAT_BOT_PATH = os.path.join(CURR_DIR, 'flat_bot.loc')
OUT_FLAT_ALL_PATH = os.path.join(CURR_DIR, 'flat_all.loc')


util.kill_ansys()
# context = NodeContext(BASE_FLAT_PATH)
# context.add_component('top_surf')
# context.add_component('bot_surf')
# context.add_component('all', elements=True)
# context.run(loglevel="INFO")

# top_df = context.result('top_surf')
# bot_df = context.result('bot_surf')
# all_df = context.result('all')

# top_df *= 0.001
# bot_df *= 0.001
# all_df *= 0.001

# top_df.to_csv(OUT_FLAT_TOP_PATH)
# bot_df.to_csv(OUT_FLAT_BOT_PATH)
# all_df.to_csv(OUT_FLAT_ALL_PATH)
