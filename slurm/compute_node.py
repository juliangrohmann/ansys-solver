import os
import env

SCRATCH_PATH = env.init_scratch()
from parametric_solver.solver import BilinearSolver
from parametric_solver.client import SolverClient


HEMJ_INP = os.path.join(SCRATCH_PATH, 'inp', 'hemj_v2.inp')
OUTPUR_DIR = os.path.join(SCRATCH_PATH, 'output')
SOLUTION_DIR = os.path.join(OUTPUR_DIR, 'solutions')
RUN_DIR = os.path.join(OUTPUR_DIR, 'err', os.environ.get("SLURM_JOB_ID"), os.environ.get("SLURM_NODEID"), os.environ.get("SLURM_PROCID"))
SERVER_IP = '128.61.254.34:41559'

exec_file = env.get_ansys_exec_file()
print(f"ANSYS executable path: {exec_file}")

# port = 50052 + int(os.environ.get("SLURM_NODEID"))
port = 50052
print(f"Port = {port}")

solver = BilinearSolver(
    HEMJ_INP,
    write_path=SOLUTION_DIR,
    exec_file=exec_file,
    run_location=RUN_DIR,
    loglevel="INFO",
    start_instance=False,
    port=port)

client = SolverClient(SERVER_IP, solver)
client.run()
