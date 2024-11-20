import os
import logging
import subprocess
import datetime
from threading import Thread
import time
import re

# CONFIG_LINE_NUM = 4
RUNNING_PROCESS = []

def set_logger(args):
    log_file = os.path.join(args.log_dir, args.log_file)
    log_level = getattr(logging, args.log_level)
    log_format = args.log_format

    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # handler
    file_handler = logging.FileHandler(log_file)
    console_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # args.std_output = True

    if args.std_output:
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

def get_process_queue(logger):
    process_queue = []
    try:
        with open("./process_queue.que", "r") as f:
            process_queue = f.readlines()
        process_queue = list(filter(lambda x: x, map(str.strip, process_queue)))
        for i, item in enumerate(process_queue):
            sid, submit_time, cwd, script, *args = item.split()
            status = args[-1]
            args = args[:-1]
            process_queue[i] = [sid, submit_time, cwd, script, args, status]
    except FileNotFoundError:
        logger.error("process_queue.que not found")
    return process_queue

def add_process_to_queue(logger, process_name):
    with open("./process_queue.que", "a") as f:
        f.write(process_name + "\n")
    logger.info(f"Added process {process_name}")

def update_process_queue(logger, process_queue):
    with open("./process_queue.que", "wt") as f:
        for item in process_queue:
            f.write(f"{item[0]:0>3}\t{item[1]:<25}{item[2]:<60}{item[3]:<60}{' '.join(item[4])}\t{item[5]}\n")
    logger.info("Updated process queue")

def get_gpu_status(logger):
    gpu_status = []
    try:
        gpu_status = subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,nounits,noheader'], text=True)
        gpu_status = gpu_status.strip().split('\n')
        gpu_status = [x.split(',') for x in gpu_status]
        gpu_status = [(int(x[0]), int(x[1])) for x in gpu_status]
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get gpu status: {e.output}")
    return gpu_status

def get_script_config(script_path):
    with open(script_path, "r") as f:
        script_config = list(filter(lambda x: x, map(str.strip, f.readlines())))
    
    configs = {}
    for config in script_config:
        if config.startswith("#SBATCH"):
            cfg = config.split()
            if cfg[1] == "CONFIG_END":
                break
            configs[cfg[1]] = cfg[2]
    return configs

def check_running_processes(logger):
    # TODO: Refine this function
    while True:
        queue = get_process_queue(logger)  # sid, submit_time, base_dir, script, args, status
        modified = False

        for process in RUNNING_PROCESS[::]:
            process: Thread
            if not process.is_alive():
                logger.info(f"Process {process.name} finished")
                for idx, item in enumerate(queue):
                    if f"{item[0]}-{item[1]}-{item[3]}" == process.name:  # thread name: sid-submit_time-script_path
                        queue[idx][-1] = "finished"
                        modified = True
                RUNNING_PROCESS.remove(process)

        if modified:
            update_process_queue(logger, queue)

        time.sleep(10)

def run_script_with_conda_env(logger, env_name, script_path, sid, kwargs):
    try:
        required_gpus = kwargs.get("gpu_num", 0)
        if required_gpus > 0:
            allocated_gpus = kwargs.get("allocated_gpus")
        else:
            allocated_gpus = []

        if allocated_gpus:
            if len(allocated_gpus) < required_gpus:
                logger.error(f"Not enough free gpus for process: {script_path}, need {required_gpus} gpus")
                return
            gpus = f"CUDA_VISIBLE_DEVICES={','.join(map(str, allocated_gpus))}"
        else:
            gpus = ""

        conda_base = subprocess.check_output(["conda", "info", "--base"], text=True).strip()
        python_excutable = os.path.join(conda_base, "envs", env_name, "bin", "python")

        with open(script_path, "r") as f:
            script_lines = f.readlines()
        
        script_base = kwargs.get("base", "./")
        tmp_script_path = "./tmp_script.sh"

        with open(tmp_script_path, "wt") as f:
            f.write(f'cd {script_base}\n')
            for line in script_lines:
                line = line.strip()
                if "python" in line:
                    line = line.replace("python", python_excutable)
                    # python_file = re.search(r"python\s+(.+\.py)", line)
                    # line = line.replace(python_file.group(1), os.path.join(script_base, python_file.group(1)))
                f.write(line + "\n")

        command = f"{gpus} bash {tmp_script_path} {' '.join(kwargs.get('args', []))}"
        logger.info(f"Running script: {script_path} submitted at {kwargs.get('submit_time')}")
        logger.info(f"Command: {command}")

        if kwargs.get("output_path") is not None:
            redirect_outf = os.path.join(script_base, kwargs["output_path"])
            # redirect_outf = kwargs["output_path"]
        else:
            redirect_outf = os.path.join(script_base, f"{sid}-{os.path.basename(script_path)}.out")
            # redirect_outf = f"{sid}-{os.path.basename(script_path)}.out"
        
        if os.path.dirname(redirect_outf):
            os.makedirs(os.path.dirname(redirect_outf), exist_ok=True)

        with open(redirect_outf, "wt") as outf:
            process = subprocess.Popen(command, shell=True, stdout=outf, stderr=outf)
            process.wait()
    except Exception as e:
        logger.error(f"Error while running script: {e.with_traceback()}")
        return

def start_process(type, logger, **kwargs):
    sid = kwargs.get("sid", None)
    if sid is None:
        logger.error("sid is required")
        return
    if type == "conda":
        if kwargs.get("env_name") is None:
            logger.error("env_name is required")
            return
        if kwargs.get("script_path") is None:
            logger.error("script_path is required")
            return
        # print("here", kwargs)
        env_name = kwargs["env_name"]
        script_path = kwargs["script_path"]
        kwargs.pop("env_name")
        kwargs.pop("script_path")
        # thread name: sid-submit_time-script_path
        t_process = Thread(target=run_script_with_conda_env, args=(logger, env_name, script_path, sid, kwargs), name=f"{sid}-{kwargs['submit_time']}-{script_path}")
        t_process.start()
        RUNNING_PROCESS.append(t_process)
    else:
        raise NotImplementedError(type)
    

if __name__ == "__main__":
    print(get_process_queue())
