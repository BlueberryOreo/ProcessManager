# Simple GPU Process Manager

A tool to manage the python processes which need GPUs on server. ~~It will support additional scripts in the future.~~

The system will automatically detect the current GPU status on the server and allocate available GPUs to processes waiting in the queue.

## Platform

Linux

## Requirements

GNU Make, GNU C++, Python>=3.5

## Installation and Running

``` shell
# Compile the cpp tools
# Make sure to replace the QUEUEPATH in each cpp file to your own path before compile. 
make
make clean_objects

# Add the current directory to environment
echo 'export PATH=$PATH:$(pwd)' >> ~/.bashrc
source ~/.bashrc

# Start the python process
nohup python main.py --max_process the_max_process_in_queue &

# Stop the python process
# Find the pid showed in log.log and kill it. 
```

## How to Use

### Script format

You should follow the file header below while writing a running script. 
``` shell
#SBATCH TYPE conda(required)
#SBATCH GPU_NUM the_gpu_num_you_need(required)
#SBATCH ENV_NAME your_conda_env_name(required)
#SBATCH OUTPUT_FILE script_output_file
#SBATCH CONFIG_END

# Your running scripts here. 
```

You can find an explicit example in [`./test.sh`](./test.sh)

### Submit a process
``` shell
submit your_script.sh args1 args2 ...

# Example
submit ./test.sh 1 2
```

### Show current process queue
``` shell
lsqueue

# Output format
# id    submimt_time    cwd     script      status
```

### Remove process(es) from the queue
``` shell
rmqueue id1 id2 ...

# Example
rmqueue 0
rmqueue 1
rmqueue 1 2 3
```