while getopts ":n:" opt; do
  case $opt in
    n)
      num_iterations="$OPTARG"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

mkdir -p ~/scratch/output/err
mkdir -p ~/scratch/output/solutions
cd  ~/scratch/output/err
rm -rf *

cd ~/scratch/slurm

for ((i=1; i<=num_iterations; i++)); do
  sbatch launch_client.sbatch
done

python head_node.py
