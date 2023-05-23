import os
import env

# Initialize environment
ROOT = env.init_root()
from parametric_solver.solver import BilinearSolver
from parametric_solver.client import SolverClient

# Initialize directories
HEMJ_INP = os.path.join(ROOT, 'inp', 'hemj_v2.inp')
OUTPUT_DIR = os.path.join(ROOT, 'output')
SOLUTION_DIR = os.path.join(OUTPUT_DIR, 'solutions')
RUN_DIR = os.path.join(OUTPUT_DIR, 'err', os.environ.get("SLURM_JOB_ID"))

# Initialize server ip/port
SERVER_IP = '128.61.254.32:41559'

# Initialize Ansys APDL installation
exec_file = env.get_ansys_exec_file()
print(f"ANSYS executable path: {exec_file}")

# Initialize local gRPC server port
port = 50052
print(f"Port = {port}")
print(f"Run directory = {RUN_DIR}")

# Initialize parametric solver
solver = BilinearSolver(
    HEMJ_INP,
    write_path=SOLUTION_DIR,
    exec_file=exec_file,
    run_location=RUN_DIR,
    loglevel="INFO",
    start_instance=False,
    port=port)

# Initialize and launch client
client = SolverClient(SERVER_IP, solver)
client.run()
