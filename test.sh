# TYPE conda
# GPU_NUM 0
# ENV_NAME cclm
# OUTPUT_FILE ./test.log
# CONFIG_END

a=$1
b=$2

echo "a = $a"
echo "b = $b"

python test.py
