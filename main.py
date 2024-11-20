import json
import os
import argparse
from threading import Thread
from utils import *

def set_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--devices", type=str, default="0", help="gpu devices")
    parser.add_argument("--interval", type=int, default=120, help="interval")
    parser.add_argument("--max_process", type=int, default=8, help="max process")
    parser.add_argument("--std_output", action='store_true', help="standard output")
    parser.add_argument("--log_file", type=str, default="log.log", help="log file")
    parser.add_argument("--log_dir", type=str, default=".", help="log dir")
    parser.add_argument("--log_level", type=str, default="INFO", help="log level")
    parser.add_argument("--log_format", type=str, default="[%(asctime)s - %(levelname)s] %(message)s", help="log format")

    args = parser.parse_args()
    return args

def run(args):
    logger = set_logger(args)
    logger.info("Start process, pid={}".format(os.getpid()))

    if not os.path.exists("./process_queue.que"):
        with open("./process_queue.que", "wt") as f:
            pass
    
    t_check_running_processes = Thread(target=check_running_processes, args=(logger,), daemon=True)
    t_check_running_processes.start()

    while True:
        gpu_status = get_gpu_status(logger)
        free_gpus = []
        for gpu_id, mem_use in enumerate(gpu_status):
            if mem_use[0] < 400:
                free_gpus.append(gpu_id)
        queue = get_process_queue(logger)
        modified = False
        if len(queue) > 0:
            logger.info(f"Current process queue size: {len(queue)}")
        
        for idx, (sid, submit_time, base_dir, process, process_args, status) in enumerate(queue[::]):
            # sid, submit_time, base_dir, process, process_args, status = item
            if status == "finished":
                queue.pop(idx)
                modified = True
                continue

            if status == "running":
                continue
            
            # Handling waiting processes
            sid = int(sid)
            script_config = get_script_config(process)
            type = script_config.get("TYPE", None)
            required_gpus = int(script_config.get("GPU_NUM", "0"))
            env_name = script_config.get("ENV_NAME", None)
            output_path = script_config.get("OUTPUT_FILE", None)

            if len(free_gpus) >= required_gpus:
                allocated_gpus = free_gpus[:required_gpus]
                free_gpus = free_gpus[required_gpus:]

                start_process(type, logger, 
                              env_name=env_name, 
                              base=base_dir,
                              script_path=process, 
                              gpu_num=required_gpus, 
                              allocated_gpus=allocated_gpus, 
                              output_path=output_path,
                              args=process_args,
                              sid=sid,
                              submit_time=submit_time)
                
                queue[idx][-1] = "running"
                modified = True
        
        if modified:
            update_process_queue(logger, queue)

        time.sleep(args.interval)

def main():
    args = set_args()
    run(args)

if __name__ == "__main__":
    main()