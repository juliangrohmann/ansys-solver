cd ~/scratch/ansys_solver/analysis_v3
mkdir out_curved_elastic
mkdir out_curved_plastic
mkdir out_flat_elastic
mkdir out_flat_plastic


cd ~/scratch/ansys_solver/analysis_v3/slurm

sbatch launch_client.sbatch curved plastic 0 25
sbatch launch_client.sbatch curved plastic 25 50
sbatch launch_client.sbatch curved plastic 50 75
sbatch launch_client.sbatch curved plastic 75 100
sbatch launch_client.sbatch curved plastic 100 125
sbatch launch_client.sbatch curved plastic 125 150
sbatch launch_client.sbatch curved plastic 150 175
sbatch launch_client.sbatch curved plastic 175 200
sbatch launch_client.sbatch curved plastic 200 225
sbatch launch_client.sbatch curved plastic 225 250
sbatch launch_client.sbatch curved plastic 250 275
sbatch launch_client.sbatch curved plastic 275 300
sbatch launch_client.sbatch curved plastic 300 325
sbatch launch_client.sbatch curved plastic 325 350
sbatch launch_client.sbatch curved plastic 350 375
sbatch launch_client.sbatch curved plastic 375 391