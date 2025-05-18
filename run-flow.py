#!/usr/bin/env python3

import os
import subprocess
import json
import shutil
import sys

# Get the current script directory.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def run_command(cmd, cwd=None):
    """Run the command and print the output."""
    print(f"Running: {cmd}")
    try:
        process = subprocess.run(cmd, shell=True, check=True, cwd=cwd, 
                                stderr=subprocess.STDOUT, stdout=subprocess.PIPE, 
                                universal_newlines=True)
        print(process.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {cmd}")
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        return False

def run_hls_commands():
    """Run HLS-related commands."""
    print("==== Running HLS commands ====")
    
    # Switch to the hls directory and execute the command.
    hls_dir = os.path.join(SCRIPT_DIR, "hls")
    
    # Enter the hls directory.
    if not os.path.exists(hls_dir):
        print(f"Error: HLS directory {hls_dir} does not exist")
        return False
    
    # Load the Catapult module and execute make.
    if not run_command("module load catapult && make", cwd=hls_dir):
        return False
    
    # Copy the generated RTL to the src directory.
    src_dir = os.path.join(SCRIPT_DIR, "src")
    concat_rtl = os.path.join(hls_dir, "Catapult/pe.v1/concat_rtl.v")
    
    if not os.path.exists(concat_rtl):
        print(f"Error: concat_rtl.v not found at {concat_rtl}")
        return False
        
    # Ensure that the src directory exists.
    os.makedirs(src_dir, exist_ok=True)
    
    # copy file
    shutil.copy(concat_rtl, os.path.join(src_dir, "concat_rtl.v"))
    print(f"Copied {concat_rtl} to {src_dir}")
    
    return True

def run_docker_commands(platform, nickname):
    """在Docker容器中运行命令"""
    print("==== Running commands in Docker container ====")
    
    # Use the correct flow/designs directory path.
    flow_dir = os.path.join(SCRIPT_DIR, "..", "flow")
    design_config_path = os.path.join(flow_dir, "designs", platform, nickname, "config.mk")
    
    # check and print whether config.mk exists.
    print(f"Checking if design config exists: {design_config_path}")
    if not os.path.exists(design_config_path):
        print(f"Warning: Design config file not found at {design_config_path}")
    else:
        print(f"Design config file exists: {design_config_path}")
    
    # Start the Docker container – no need to mount the designs directory separately, 
    # as the flow directory is already mounted.
    docker_cmd = (
        "docker run --rm -it -e DISPLAY=$DISPLAY "
        "-e QT_XCB_FORCE_SOFTWARE_OPENGL=1 -e XDG_RUNTIME_DIR=/tmp/runtime-root "
        "-v /tmp/.X11-unix:/tmp/.X11-unix -v ${HOME}/.Xauthority:/root/.Xauthority "
        "-v $(pwd)/flow:/OpenROAD-flow-scripts/flow --net=host "
        "openroad/flow-ubuntu22.04-builder:bb283b "
        f"/bin/bash -c 'cd /OpenROAD-flow-scripts && "
        f"source ./env.sh && "
        f"cd flow && "
        # f"make clean_all DESIGN_CONFIG=designs/{platform}/{nickname}/config.mk && "
        f"make DESIGN_CONFIG=designs/{platform}/{nickname}/config.mk'"
    )
    
    # Note: Here we start Docker in interactive mode, so the script will wait 
    # at this point until the Docker container finishes running.
    return run_command(docker_cmd, cwd=os.path.join(SCRIPT_DIR, ".."))

def main():
    # Run the HLS command first.
    if not run_hls_commands():
        print("Error during HLS commands, stopping execution")
        sys.exit(1)
    
    print("\n==== Running main flow ====")
    
    # Run the Python scripts in order.
    scripts_dir = os.path.join(SCRIPT_DIR, "scripts")
    run_command("python3 setup_configmk.py", cwd=scripts_dir)
    run_command("python3 parse_verilog.py", cwd=scripts_dir)
    run_command("python3 systolic_array_generator.py", cwd=scripts_dir)
    run_command("python3 generate_top.py", cwd=scripts_dir)
    
    # Parse setup.json.
    setup_file = os.path.join(SCRIPT_DIR, "setup.json")
    with open(setup_file, 'r') as f:
        setup_data = json.load(f)
    
    # Extract values.
    platform = setup_data.get("config_mk", {}).get("PLATFORM")
    design_name = setup_data.get("config_mk", {}).get("DESIGN_NAME")
    nickname = setup_data.get("config_mk", {}).get("DESIGN_NICKNAME")
    
    # Check whether the necessary values have been retrieved.
    if not platform or not nickname:
        print(f"Error: PLATFORM or DESIGN_NICKNAME not found in {setup_file}")
        sys.exit(1)
    
    # Create the design directory – modify the path to ../flow/designs/.
    flow_dir = os.path.join(SCRIPT_DIR, "..", "flow")
    design_dir = os.path.join(flow_dir, "designs", platform, nickname)
    src_dir = os.path.join(flow_dir, "designs", "src", nickname)
    
    # Ensure the directory exists.
    os.makedirs(design_dir, exist_ok=True)
    os.makedirs(src_dir, exist_ok=True)
    
    # Check whether the files in the build directory exist.
    config_mk_path = os.path.join(SCRIPT_DIR, "build", "config.mk")
    constraint_sdc_path = os.path.join(SCRIPT_DIR, "build", "constraint.sdc")
    block_mk_path = os.path.join(SCRIPT_DIR, "build", "block.mk")
    verilog_path = os.path.join(SCRIPT_DIR, "build", f"{design_name}.v")
    
    if not os.path.exists(block_mk_path):
       print(f"Error: {block_mk_path} not found")

    if not os.path.exists(config_mk_path):
        print(f"Error: {config_mk_path} not found")
        sys.exit(1)
    
    if not os.path.exists(constraint_sdc_path):
        print(f"Error: {constraint_sdc_path} not found")
        sys.exit(1)
    
    if not os.path.exists(verilog_path):
        print(f"Error: {verilog_path} not found")
        sys.exit(1)
    
    # Copy the files.
    shutil.copy(config_mk_path, os.path.join(design_dir, "config.mk"))
    shutil.copy(block_mk_path, os.path.join(design_dir, "block.mk"))
    shutil.copy(constraint_sdc_path, os.path.join(design_dir, "constraint.sdc"))
    
    # Copy the verilog files.
    shutil.copy(verilog_path, os.path.join(src_dir, f"{design_name}.v"))
    
    # Copy all .v files from the src directory.
    src_verilog_dir = os.path.join(SCRIPT_DIR, "src")
    for file in os.listdir(src_verilog_dir):
        if file.endswith(".v"):
            shutil.copy(os.path.join(src_verilog_dir, file), 
                        os.path.join(src_dir, file))
    
    # Update the directory mount in the Docker command.
    if not run_docker_commands(platform, nickname):
        print("Error during Docker execution, stopping script")
        sys.exit(1)

if __name__ == "__main__":
    main() 
