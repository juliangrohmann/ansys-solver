mkdir -p ~/scratch/output/err
cd  ~/scratch/output/err
rm -rf *

mkdir -p ~/scratch/output/out
cd  ~/scratch/output/out
rm -rf *


cd ~/scratch/ansys_solver/analysis_v3
mkdir out_curved_elastic
mkdir out_curved_plastic
mkdir out_flat_elastic
mkdir out_flat_plastic


cd ~/scratch/ansys_solver/analysis_v3/slurm

sbatch launch_client.sbatch curved elastic 0 50
sbatch launch_client.sbatch curved elastic 50 100

sbatch launch_client.sbatch flat elastic 0 50
sbatch launch_client.sbatch flat elastic 50 100

sbatch launch_client.sbatch curved plastic 0 50
sbatch launch_client.sbatch curved plastic 50 100
sbatch launch_client.sbatch curved plastic 100 150
sbatch launch_client.sbatch curved plastic 150 200
sbatch launch_client.sbatch curved plastic 200 250
sbatch launch_client.sbatch curved plastic 250 300
sbatch launch_client.sbatch curved plastic 300 350
sbatch launch_client.sbatch curved plastic 350 400
sbatch launch_client.sbatch curved plastic 400 450
sbatch launch_client.sbatch curved plastic 450 500

sbatch launch_client.sbatch flat plastic 0 50
sbatch launch_client.sbatch flat plastic 50 100
sbatch launch_client.sbatch flat plastic 100 150
sbatch launch_client.sbatch flat plastic 150 200
sbatch launch_client.sbatch flat plastic 200 250
sbatch launch_client.sbatch flat plastic 250 300
sbatch launch_client.sbatch flat plastic 300 350
sbatch launch_client.sbatch flat plastic 350 400
sbatch launch_client.sbatch flat plastic 400 450
sbatch launch_client.sbatch flat plastic 450 500
