import os
import env

SCRATCH_PATH = env.init_scratch()
# SCRATCH_PATH = env.init_root()
from parametric_solver.solver import BilinearSolver
from parametric_solver.client import SolverClient


HEMJ_INP = os.path.join(SCRATCH_PATH, 'inp', 'hemj_v2.inp')
OUTPUR_DIR = os.path.join(SCRATCH_PATH, 'output')
SOLUTION_DIR = os.path.join(OUTPUR_DIR, 'solutions')

RUN_DIR = os.path.join(OUTPUR_DIR, os.environ.get("SLURM_JOB_ID"))
# RUN_DIR = os.path.join(OUTPUR_DIR, 'err', '1')

SERVER_IP = '128.61.254.34:41559'
# SERVER_IP = '127.0.0.1:5000'

env.init_ansys()

solver = BilinearSolver(
    HEMJ_INP,
    write_path=SOLUTION_DIR,
    run_location=RUN_DIR,
    loglevel="INFO",
    start_instance=False)

client = SolverClient(SERVER_IP, solver)
client.run()
