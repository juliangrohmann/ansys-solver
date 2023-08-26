cd ~/scratch/ansys_solver/analysis_v3
mkdir out_curved_elastic
mkdir out_curved_plastic
mkdir out_flat_elastic
mkdir out_flat_plastic


cd ~/scratch/ansys_solver/analysis_v3/slurm

sbatch launch_client.sbatch flat plastic 0 25
sbatch launch_client.sbatch flat plastic 25 50
sbatch launch_client.sbatch flat plastic 50 75
sbatch launch_client.sbatch flat plastic 75 100
sbatch launch_client.sbatch flat plastic 100 125
sbatch launch_client.sbatch flat plastic 125 150
sbatch launch_client.sbatch flat plastic 150 175
sbatch launch_client.sbatch flat plastic 175 200
sbatch launch_client.sbatch flat plastic 200 225
sbatch launch_client.sbatch flat plastic 225 250
sbatch launch_client.sbatch flat plastic 250 275
sbatch launch_client.sbatch flat plastic 275 300
sbatch launch_client.sbatch flat plastic 300 325
sbatch launch_client.sbatch flat plastic 325 350
sbatch launch_client.sbatch flat plastic 350 375
sbatch launch_client.sbatch flat plastic 375 391