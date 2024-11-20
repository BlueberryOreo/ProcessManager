#SBATCH TYPE conda
#SBATCH GPU_NUM 0
#SBATCH ENV_NAME cclm
#SBATCH OUTPUT_FILE ./test.log
#SBATCH CONFIG_END

a=$1
b=$2

echo "a = $a"
echo "b = $b"

python test.py
