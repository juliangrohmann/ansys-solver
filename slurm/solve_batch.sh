mkdir -p ~/scratch/output/err
mkdir -p ~/scratch/output/solutions
cd  ~/scratch/output/err
rm -rf *

cd ~/scratch/slurm

for i in {1..4}; do
    sbatch launch_client.sbatch
done

python head_node.py
