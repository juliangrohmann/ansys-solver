#!/bin/bash
#SBATCH  -J9
#SBATCH  --account=gts-my14-paid
#SBATCH  -q inferno
#SBATCH  -opace.out-%j.out
#SBATCH  -t02:30:00
#SBATCH  --mem-per-cpu=4G
#SBATCH  -N1 --ntasks-per-node=4

cd $SLURM_SUBMIT_DIR
module load ansys/2021R2
fluent 2ddp -t4 -mpi=intel -cnf=$SLURM_JOB_NODELIST  -g < fluent.input > outputfile
