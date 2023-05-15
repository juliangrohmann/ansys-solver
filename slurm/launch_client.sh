cd ~/scratch/output/err
mkdir -p ${SLURM_JOB_ID}/${SLURM_NODEID}/${SLURM_PROCID}
cd ${SLURM_JOB_ID}/${SLURM_NODEID}/${SLURM_PROCID}
echo ${SLURM_JOB_ID}/${SLURM_NODEID}/${SLURM_PROCID}
rm -rf *

#"/usr/local/pace-apps/manual/packages/ansys/2023R1/v231/ansys/bin/ansys231" -j file -np 4 -port 50052 -grpc &
#sleep 60
#echo "Launched gRPC server on node ${SLURM_NODEID}, process ${SLURM_PROCID}"

module load ansys/2023R1

"/usr/local/pace-apps/manual/packages/ansys/2023R1/v231/ansys/bin/ansys231" -j file -np 4 -port 50052 -grpc &

#cd ~/scratch
#source venv/bin/activate
#python slurm/debug.py
#python slurm/compute_node.py