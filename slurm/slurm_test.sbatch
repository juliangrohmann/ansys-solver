#!/bin/bash
#SBATCH -J slurm_test
#SBATCH --account=gts-my14
#SBATCH -q embers
#SBATCH --mem-per-cpu=4G
#SBATCH -N1 --ntasks-per-node=1
#SBATCH -t 0-00:30:00
#SBATCH -o %j.out
#SBATCH --mail-type=ALL

cd ~/scratch
module load ansys/2023R1
source venv/bin/activate
srun python slurm/slurm_test.py
