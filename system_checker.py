import os
import psutil
import platform
import subprocess

# Define minimum requirements
MIN_CPU_CORES = 4
MIN_RAM_GB = 16
MIN_GPU_MEMORY_MB = 8000
REQUIRED_PYTHON_VERSION = "3.8"
REQUIRED_LIBRARIES = ["ollama"]

def check_hardware_requirements():
    # Check CPU
    cpu_cores = psutil.cpu_count(logical=True)
    print(f"CPU Cores: {cpu_cores}")
    if cpu_cores < MIN_CPU_CORES:
        print(f"Insufficient CPU cores. Minimum required: {MIN_CPU_CORES}")
        return False

    # Check RAM
    ram = psutil.virtual_memory().total / (1024 ** 3)  # Convert bytes to GB
    print(f"RAM: {ram:.2f} GB")
    if ram < MIN_RAM_GB:
        print(f"Insufficient RAM. Minimum required: {MIN_RAM_GB} GB")
        return False

    # Check GPU (if available)
    try:
        gpu_info = subprocess.check_output(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]).decode().strip()
        gpus = gpu_info.split('\n')
        for i, gpu in enumerate(gpus):
            name, memory = gpu.split(',')
            memory = int(memory.strip())
            print(f"GPU {i}: {name.strip()} with {memory} MB memory")
            if memory < MIN_GPU_MEMORY_MB:
                print(f"Insufficient GPU memory. Minimum required: {MIN_GPU_MEMORY_MB} MB")
                return False
    except FileNotFoundError:
        print("No NVIDIA GPU found or `nvidia-smi` not installed.")
        return False

    return True

def check_software_requirements():
    # Check Python version
    python_version = platform.python_version()
    print(f"Python Version: {python_version}")
    if python_version < REQUIRED_PYTHON_VERSION:
        print(f"Insufficient Python version. Minimum required: {REQUIRED_PYTHON_VERSION}")
        return False

    # Check for required libraries
    for lib in REQUIRED_LIBRARIES:
        try:
            __import__(lib)
            print(f"Library '{lib}' is installed.")
        except ImportError:
            print(f"Library '{lib}' is NOT installed.")
            return False

    return True

if __name__ == "__main__":
    print("Checking hardware requirements...")
    hardware_ok = check_hardware_requirements()
    print("\nChecking software requirements...")
    software_ok = check_software_requirements()

    if hardware_ok and software_ok:
        print("\nSystem meets the requirements to run `mistral-small:22b-instruct-2409-q8_0`.")
    else:
        print("\nSystem does NOT meet the requirements to run `mistral-small:22b-instruct-2409-q8_0`.")