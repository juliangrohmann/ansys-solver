#!/bin/bash
#SBATCH -J slurm_test
#SBATCH --account=gts-my14
#SBATCH -q inferno
#SBATCH --mem-per-cpu=4G
#SBATCH --cpus-per-task=4
#SBATCH --nodes=4
#SBATCH --ntasks-per-node=1
#SBATCH -t 0-00:30:00
#SBATCH -o %j.out
#SBATCH --mail-type=ALL
#SBATCH --output=%j_out.log
#SBATCH --error=%j_err.log

module load ansys/2023R1
srun ./launch_client.sh
