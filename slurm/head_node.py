import numpy as np
import env

# Initialize environment
SCRATCH_PATH = env.init_scratch()
from parametric_solver.server import SolverServer

# Initialize server
server = SolverServer()

# Add samples to server
tangent_mods = np.linspace(50e9, 160e9, 12)
for tangent_mod in tangent_mods:
    server.add_sample((200e9, 700e6, tangent_mod))

# Start serrver and listen on all IPs
server.run(host='0.0.0.0', port=41559)
