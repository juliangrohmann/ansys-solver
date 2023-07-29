#!/bin/bash
#SBATCH -J hemj_curved_elastic
#SBATCH --account=gts-my14
#SBATCH -q inferno
#SBATCH --mem-per-cpu=8G
#SBATCH --cpus-per-task=8
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH -t 1-00:00:00
#SBATCH -o %j.out
#SBATCH --mail-type=ALL
#SBATCH --output=%j_out.log
#SBATCH --error=%j_err.log

module load ansys/2023R1

cd ~/scratch
source venv/bin/activate
python ansys_solver/analysis_v3/solve.py $1 $2 $3 $4