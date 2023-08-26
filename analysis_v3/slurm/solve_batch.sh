cd ~/scratch/ansys_solver/analysis_v3
mkdir out_curved_elastic
mkdir out_curved_plastic
mkdir out_flat_elastic
mkdir out_flat_plastic


cd ~/scratch/ansys_solver/analysis_v3/slurm

sbatch launch_client.sbatch curved elastic 0 25
sbatch launch_client.sbatch curved elastic 25 50
sbatch launch_client.sbatch curved elastic 50 75
sbatch launch_client.sbatch curved elastic 75 100
sbatch launch_client.sbatch curved elastic 100 125
sbatch launch_client.sbatch curved elastic 125 150
sbatch launch_client.sbatch curved elastic 150 175
sbatch launch_client.sbatch curved elastic 175 200
sbatch launch_client.sbatch curved elastic 200 225
sbatch launch_client.sbatch curved elastic 225 250
sbatch launch_client.sbatch curved elastic 250 275
sbatch launch_client.sbatch curved elastic 275 300
sbatch launch_client.sbatch curved elastic 300 325
sbatch launch_client.sbatch curved elastic 325 350
sbatch launch_client.sbatch curved elastic 350 375
sbatch launch_client.sbatch curved elastic 375 391