from threading import Thread
from abc import ABC, abstractmethod
import subprocess
import os
import time

class Process(Thread, ABC):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.start_time = None  # time when the process started

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def terminate(self):
        pass

class CondaProcess(Process):
    def __init__(self, name, logger, env_name, script_path, sid, kwargs):
        super().__init__(name)
        self.logger = logger
        self.env_name = env_name
        self.script_path = script_path
        self.sid = sid
        self.kwargs = kwargs
        self.process = None
        self.tmp_script_path = f"./tmp/tmp_script_{name}.sh"
        self.script_base = self.kwargs.get("base", "./")

        # Create a temporary script file and copy the content of the original script file to it
        conda_base = subprocess.check_output(["conda", "info", "--base"], text=True).strip()
        python_excutable = os.path.join(conda_base, "envs", self.env_name, "bin", "python")

        with open(self.script_path, "r") as f:
            script_lines = f.readlines()

        with open(self.tmp_script_path, "wt") as f:
            f.write(f'cd {self.script_base}\n')
            for line in script_lines:
                line = line.strip()
                if "python" in line:
                    line = line.replace("python", python_excutable)
                f.write(line + "\n")

    def run(self):
        try:
            required_gpus = self.kwargs.get("gpu_num", 0)
            
            if required_gpus > 0:
                allocated_gpus = self.kwargs.get("allocated_gpus")
            else:
                allocated_gpus = []

            if allocated_gpus:
                if len(allocated_gpus) < required_gpus:
                    self.logger.error(f"Not enough free gpus for process: {self.script_path}, need {required_gpus} gpus")
                    return
                gpus = f"CUDA_VISIBLE_DEVICES={','.join(map(str, allocated_gpus))}"
            else:
                gpus = ""

            command = f"{gpus} bash {self.tmp_script_path} {' '.join(self.kwargs.get('args', []))}"
            self.logger.info(f"Running script: {self.script_path} submitted at {self.kwargs.get('submit_time')}")
            self.logger.info(f"Command: {command}")

            if self.kwargs.get("output_path") is not None:
                redirect_outf = os.path.join(self.script_base, self.kwargs["output_path"])
                # redirect_outf = kwargs["output_path"]
            else:
                redirect_outf = os.path.join(self.script_base, f"{self.sid}-{os.path.basename(self.script_path)}.out")
                # redirect_outf = f"{sid}-{os.path.basename(script_path)}.out"
            
            if os.path.dirname(redirect_outf):
                os.makedirs(os.path.dirname(redirect_outf), exist_ok=True)

            with open(redirect_outf, "wt") as outf:
                self.process = subprocess.Popen(command, shell=True, stdout=outf, stderr=outf)
                self.process.wait()
        except Exception as e:
            self.logger.error(f"Error while running script {self.script_path}: {e.with_traceback()}")
            return

    def terminate(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.logger.info(f"Terminated process: {self.script_path}")

    def __del__(self):
        if os.path.exists(self.tmp_script_path):
            os.remove(self.tmp_script_path)
        self.terminate()
        self.join()
