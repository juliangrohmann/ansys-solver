import numpy as np
import env

SCRATCH_PATH = env.init_scratch()
# env.init_root()
from parametric_solver.server import SolverServer

server = SolverServer()

tangent_mods = np.linspace(50e9, 160e9, 12)
for tangent_mod in tangent_mods:
    server.add_sample((200e9, 700e6, tangent_mod))

server.run(host='0.0.0.0', port=41559)
