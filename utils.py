import os
import logging
import subprocess
import datetime
from threading import Thread
import time
import re

from process import Process, CondaProcess

# CONFIG_LINE_NUM = 4
RUNNING_PROCESS = {}

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
            process_queue[i] = [int(sid), submit_time, cwd, script, args, status]
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
            f.write(f"{item[0]:0>3}\t{item[1]:<25}{item[2]:<60}{item[3] + ' ' + ' '.join(item[4]):<60}\t{item[5]}\n")
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

def get_name(q_item):
    return f"{q_item[0]}-{q_item[1]}"

class Manager:
    def __init__(self, logger, interval):
        self.logger = logger
        self.interval = interval
        self.running = True
    
    def loop(self):
        while self.running:
            interval = self.interval
            gpu_status = get_gpu_status(self.logger)
            free_gpus = []
            for gpu_id, mem_use in enumerate(gpu_status):
                if mem_use[0] < 400:
                    free_gpus.append(gpu_id)
            queue = get_process_queue(self.logger)
            modified = False
            if len(queue) > 0:
                self.logger.info(f"Current process queue size: {len(queue)}, free gpus: {len(free_gpus)}")

            removed_idx = []
            for idx, (sid, submit_time, base_dir, q_process, process_args, status) in enumerate(queue):
                name = get_name(queue[idx])
                process: Process = RUNNING_PROCESS.get(name, None)
                if process:
                    if status == "waiting":
                        # Check if there is enough free gpus
                        required_gpus = process.required_gpus
                        if required_gpus <= len(free_gpus):
                            allocated_gpus = free_gpus[:required_gpus]
                            free_gpus = free_gpus[required_gpus:]
                            process.kwargs["allocated_gpus"] = allocated_gpus
                            process.start()
                            queue[idx][-1] = "running"
                            modified = True
                    else:
                        if not process.is_alive():
                            self.logger.info(f"Process {process.name} finished")
                            queue[idx][-1] = "finished"
                            modified = True
                            RUNNING_PROCESS.pop(name)

                        if status == "terminating" and process.is_alive():
                            self.logger.info(f"Terminating process: {process.name}")
                            process.terminate()
                            queue[idx][-1] = "finished"
                            modified = True
                            RUNNING_PROCESS.pop(name)

                else:
                    # The process is not in the RUNNING_PROCESS list
                    process = q_process

                    if status == "finished":
                        removed_idx.append(idx)
                        modified = True

                    elif status == "running" or status == "pending":
                        self.logger.warning(f"Process {name} is not in the RUNNING_PROCESS list but status is {status}")
                        self.logger.warning(f"Removing process {name} from queue")
                        removed_idx.append(idx)
                        modified = True

                    elif status == "waiting":
                        # Handling waiting processes
                        sid = int(sid)
                        script_config = get_script_config(process)
                        type = script_config.get("TYPE", None)
                        required_gpus = int(script_config.get("GPU_NUM", "0"))
                        env_name = script_config.get("ENV_NAME", None)
                        output_path = script_config.get("OUTPUT_FILE", None)
                        try:
                            self.add_process(type, 
                                            name,
                                            env_name=env_name, 
                                            base=base_dir,
                                            script_path=process, 
                                            gpu_num=required_gpus, 
                                            allocated_gpus=[], 
                                            output_path=output_path,
                                            args=process_args,
                                            sid=sid,
                                            submit_time=submit_time)
                            # queue[idx][-1] = "pending"
                            # modified = True
                            interval = 2
                        except NotImplementedError as e:
                            self.logger.error(e)
                            removed_idx.append(idx)
                            modified = True

                    else:
                        self.logger.error(f"Unknown status: {status}")
                        removed_idx.append(idx)
                        modified = True
            
            if modified:
                for idx in removed_idx:
                    queue.pop(idx)
                update_process_queue(self.logger, queue)
            
            time.sleep(interval)

    def add_process(self, type, name, **kwargs):
        sid = kwargs.get("sid", None)
        if sid is None:
            self.logger.error("sid is required")
            return
        if type == "conda":
            if kwargs.get("env_name") is None:
                self.logger.error("env_name is required")
                return
            if kwargs.get("script_path") is None:
                self.logger.error("script_path is required")
                return

            env_name = kwargs["env_name"]
            script_path = kwargs["script_path"]
            kwargs.pop("env_name")
            kwargs.pop("script_path")
            
            t_process = CondaProcess(name, self.logger, env_name, script_path, sid, kwargs)
            # t_process.start()
            # RUNNING_PROCESS.append(t_process)
            RUNNING_PROCESS[t_process.name] = t_process
        else:
            raise NotImplementedError(type)
        
        pass

# def check_running_processes(logger):
#     # TODO: Refine this function
#     while True:
#         queue = get_process_queue(logger)  # sid, submit_time, base_dir, script, args, status
#         modified = False

#         # for process in RUNNING_PROCESS[::]:
#         #     process: Process
#         #     if not process.is_alive():
#         #         logger.info(f"Process {process.name} finished")
#         #         for idx, item in enumerate(queue):
#         #             if f"{item[0]}-{item[1]}-{item[3]}" == process.name:  # thread name: sid-submit_time-script_path
#         #                 queue[idx][-1] = "finished"
#         #                 modified = True
#         #         RUNNING_PROCESS.remove(process)
#         for idx, item in enumerate(queue):
#             name = f"{item[0]}-{item[1]}-{item[3]}"
#             status = item[-1]
#             process: Process = RUNNING_PROCESS.get(name, None)
#             if process:
#                 if not process.is_alive():
#                     logger.info(f"Process {process.name} finished")
#                     queue[idx][-1] = "finished"
#                     modified = True
#                     RUNNING_PROCESS.pop(name)
#                 if status == "terminating":
#                     process.terminate()
#                     logger.info(f"Terminating process: {process.name}")
#                     queue[idx][-1] = "finished"
#                     modified = True
#                     RUNNING_PROCESS.pop(name)
#         if modified:
#             update_process_queue(logger, queue)

#         time.sleep(10)

# def run_script_with_conda_env(logger, env_name, script_path, sid, kwargs):
#     try:
#         required_gpus = kwargs.get("gpu_num", 0)
#         if required_gpus > 0:
#             allocated_gpus = kwargs.get("allocated_gpus")
#         else:
#             allocated_gpus = []

#         if allocated_gpus:
#             if len(allocated_gpus) < required_gpus:
#                 logger.error(f"Not enough free gpus for process: {script_path}, need {required_gpus} gpus")
#                 return
#             gpus = f"CUDA_VISIBLE_DEVICES={','.join(map(str, allocated_gpus))}"
#         else:
#             gpus = ""

#         conda_base = subprocess.check_output(["conda", "info", "--base"], text=True).strip()
#         python_excutable = os.path.join(conda_base, "envs", env_name, "bin", "python")

#         with open(script_path, "r") as f:
#             script_lines = f.readlines()
        
#         script_base = kwargs.get("base", "./")
#         tmp_script_path = "./tmp_script.sh"

#         with open(tmp_script_path, "wt") as f:
#             f.write(f'cd {script_base}\n')
#             for line in script_lines:
#                 line = line.strip()
#                 if "python" in line:
#                     line = line.replace("python", python_excutable)
#                     # python_file = re.search(r"python\s+(.+\.py)", line)
#                     # line = line.replace(python_file.group(1), os.path.join(script_base, python_file.group(1)))
#                 f.write(line + "\n")

#         command = f"{gpus} bash {tmp_script_path} {' '.join(kwargs.get('args', []))}"
#         logger.info(f"Running script: {script_path} submitted at {kwargs.get('submit_time')}")
#         logger.info(f"Command: {command}")

#         if kwargs.get("output_path") is not None:
#             redirect_outf = os.path.join(script_base, kwargs["output_path"])
#             # redirect_outf = kwargs["output_path"]
#         else:
#             redirect_outf = os.path.join(script_base, f"{sid}-{os.path.basename(script_path)}.out")
#             # redirect_outf = f"{sid}-{os.path.basename(script_path)}.out"
        
#         if os.path.dirname(redirect_outf):
#             os.makedirs(os.path.dirname(redirect_outf), exist_ok=True)

#         with open(redirect_outf, "wt") as outf:
#             process = subprocess.Popen(command, shell=True, stdout=outf, stderr=outf)
#             process.wait()
#     except Exception as e:
#         logger.error(f"Error while running script: {e.with_traceback()}")
#         return

# def start_process(type, logger, **kwargs):
#     sid = kwargs.get("sid", None)
#     if sid is None:
#         logger.error("sid is required")
#         return
#     if type == "conda":
#         if kwargs.get("env_name") is None:
#             logger.error("env_name is required")
#             return
#         if kwargs.get("script_path") is None:
#             logger.error("script_path is required")
#             return
#         # print("here", kwargs)
#         env_name = kwargs["env_name"]
#         script_path = kwargs["script_path"]
#         kwargs.pop("env_name")
#         kwargs.pop("script_path")
#         # thread name: sid-submit_time-script_path
#         # t_process = Thread(target=run_script_with_conda_env, args=(logger, env_name, script_path, sid, kwargs), name=f"{sid}-{kwargs['submit_time']}-{script_path}")
#         # t_process.start()
#         t_process = CondaProcess(f"{sid}-{kwargs['submit_time']}-{script_path}", logger, env_name, script_path, sid, kwargs)
#         t_process.start()
#         # RUNNING_PROCESS.append(t_process)
#         RUNNING_PROCESS[t_process.name] = t_process
#     else:
#         raise NotImplementedError(type)
    

if __name__ == "__main__":
    print(get_process_queue())
