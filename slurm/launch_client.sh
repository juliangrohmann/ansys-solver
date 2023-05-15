cd ~/scratch/output/err
mkdir -p ${SLURM_JOB_ID}/${SLURM_NODEID}/${SLURM_PROCID}
cd ${SLURM_JOB_ID}/${SLURM_NODEID}/${SLURM_PROCID}
echo ${SLURM_JOB_ID}/${SLURM_NODEID}/${SLURM_PROCID}
rm -rf *

#"/usr/local/pace-apps/manual/packages/ansys/2023R1/v231/ansys/bin/ansys231" -j file -np 4 -port 50052 -grpc &
#sleep 60
#echo "Launched gRPC server on node ${SLURM_NODEID}, process ${SLURM_PROCID}"

module load ansys/2023R1
module unload intel/20.0.4
module load openmpi/4.1.4
#module load mvapich2/2.3.6-ouywal

export OMPI_MCA_btl_base_warn_component_unused=0
export OMPI_MCA_mpi_warn_on_fork=0
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/pace-apps/manual/packages/openmpi/4.1.4/gcc-10.3.0/lib

"/usr/local/pace-apps/manual/packages/ansys/2023R1/v231/ansys/bin/ansys231" -j file -port 50052 -grpc

#cd ~/scratch
#source venv/bin/activate
#python slurm/debug.py
#python slurm/compute_node.py