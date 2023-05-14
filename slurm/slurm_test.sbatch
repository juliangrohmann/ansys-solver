#!/bin/bash
#SBATCH -J slurm_test
#SBATCH --account=gts-my14
#SBATCH -q embers
#SBATCH --mem-per-cpu=4G
#SBATCH --cpus-per-task=4
#SBATCH -N1 --ntasks-per-node=1
#SBATCH -t 0-00:30:00
#SBATCH -o %j.out
#SBATCH --mail-type=ALL
#SBATCH --output=%j_out.log
#SBATCH --error=%j_err.log

module load ansys/2023R1

cd ~/scratch/output
mkdir -p "${SLURM_JOB_ID}"
cd "${SLURM_JOB_ID}"
"/usr/local/pace-apps/manual/packages/ansys/2023R1/v231/ansys/bin/ansys231" -j file -np 4 -port 50052 -grpc &

sleep 60

cd ~/scratch
source venv/bin/activate
srun python slurm/compute_node.py

python slurm/head_node.py
