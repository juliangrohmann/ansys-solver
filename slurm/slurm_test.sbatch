#!/bin/bash
#SBATCH -J slurm_test
#SBATCH --account=gts-my14
#SBATCH -q embers
#SBATCH --mem-per-cpu=4G
#SBATCH -N1 --ntasks-per-node=1
#SBATCH -t 0-00:30:00
#SBATCH -o %j.out
#SBATCH --mail-type=ALL

module load ansys/2021R1

cd ~/scratch/output
"/usr/local/pace-apps/manual/packages/ansys/2023R1/v231/ansys/bin/ansys231" -j file -np 2   -port 50052 -grpc &

cd ~/scratch
source venv/bin/activate
srun python slurm/slurm_test.py
