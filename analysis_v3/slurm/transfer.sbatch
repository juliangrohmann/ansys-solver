#!/bin/bash
#SBATCH -J hemj_curved_elastic
#SBATCH --account=gts-my14-paid
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

cd ~/scratch/box_cli
./rclone copy ~/scratch/ansys_solver/analysis_v3/out_curved_plastic hemj_box:structural_simulation_data/curved_plastic_v3
