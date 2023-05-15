mkdir -p ~/scratch/output/err
mkdir -p ~/scratch/output/solutions
cd  ~/scratch/output/err
rm -rf *

cd ~/scratch/slurm
sbatch launch_clients.sbatch
python head_node.py
