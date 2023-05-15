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

srun bash -c 'cd ~/scratch/output/err; \
mkdir -p "${SLURM_JOB_ID}/${SLURM_NODEID}/${SLURM_PROCID}"; \
cd "${SLURM_JOB_ID}/${SLURM_NODEID}/${SLURM_PROCID}"; \
echo "${SLURM_JOB_ID}/${SLURM_NODEID}/${SLURM_PROCID}"; \
"/usr/local/pace-apps/manual/packages/ansys/2023R1/v231/ansys/bin/ansys231" -j file -np 4 -port $((50052+SLURM_NODEID)) -grpc & \
sleep 60; \
echo "Launched gRPC server on node ${SLURM_NODEID}, process ${SLURM_PROCID}"'

cd ~/scratch
source venv/bin/activate
srun python slurm/compute_node.py
