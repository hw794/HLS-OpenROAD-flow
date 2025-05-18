#!/usr/bin/env python3
"""
Standard version of the Systolic Array generator
Handles standard naming conventions (left_in, right_out, up_in, down_out, etc.)
"""
import yaml
import json
import re
import os
import sys

def generate_systolic_array_json(yaml_file, pe_config_file, json_file):
    """
        Generate a JSON description of the systolic array based on the YAML configuration file and the PE module configuration.

        Parameters:

        -yaml_file - Path to the YAML file containing high-level configuration
        -pe_config_file - Path to the JSON file containing PE module port definitions
        -json_file - Path to the output JSON file
    """
    # Load YAML configuration
    with open(yaml_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Load PE module configuration
    with open(pe_config_file, 'r') as f:
        pe_config = json.load(f)
    
    # Initialize JSON structure
    json_data = {
        "top_module": config["top_module"],
        "top_ports": {},
        "instances": {}
    }
    
    # Process top ports
    for port in config.get("top_ports", []):
        json_data["top_ports"][port["name"]] = {
            "direction": port["direction"],
            "width": port["width"]
        }
    
    # Get dimensions from YAML
    dimensions = config["dimensions"]
    rows, cols = dimensions[0], dimensions[1]
    
    # Extract port names and info from PE config
    pe_ports = pe_config["ports"]
    
    # Copy all fields from the original port definitions
    def create_port_copy(port_info):
        return {key: value for key, value in port_info.items()}
    
    # Standard port groupings
    port_groups = {
        "left": [name for name in pe_ports if name.startswith("left_in")],
        "right": [name for name in pe_ports if name.startswith("right_out")],
        "up": [name for name in pe_ports if name.startswith("up_in")],
        "down": [name for name in pe_ports if name.startswith("down_out")],
        "result": [name for name in pe_ports if name.startswith("result_out")]
    }
    
    # Basic control ports
    control_ports = ["clk", "rst"]
    
    # Add top-level ports for the systolic array
    for i in range(rows):
        # Left edge input ports
        for port in port_groups["left"]:
            suffix = port.split("_rsc")[1] if "_rsc" in port else ""
            port_info = create_port_copy(pe_ports[port])
            
            # Create port with index
            port_name = f"{port.split('_rsc')[0]}_rsc{i}{suffix}"
            json_data["top_ports"][port_name] = port_info
        
        # Right edge output ports
        for port in port_groups["right"]:
            suffix = port.split("_rsc")[1] if "_rsc" in port else ""
            port_info = create_port_copy(pe_ports[port])
            
            # Correction: ensure the directions are correct.
            # The previous inversion logic was incorrect: 
            # for output ports, dat and vld should remain as output, 
            # while rdy should remain as input.
            # port_info["direction"] = "input" if port_info["direction"] == "output" else "output"
            
            port_name = f"{port.split('_rsc')[0]}_rsc{i}{suffix}"
            json_data["top_ports"][port_name] = port_info
    
    for j in range(cols):
        # Top edge input ports
        for port in port_groups["up"]:
            suffix = port.split("_rsc")[1] if "_rsc" in port else ""
            port_info = create_port_copy(pe_ports[port])
            
            port_name = f"{port.split('_rsc')[0]}_rsc{j}{suffix}"
            json_data["top_ports"][port_name] = port_info
        
        # Bottom edge output ports
        for port in port_groups["down"]:
            suffix = port.split("_rsc")[1] if "_rsc" in port else ""
            port_info = create_port_copy(pe_ports[port])
            
            # Correction: ensure the directions are correct.
            #The previous inversion logic was incorrect: for output ports, 
            # dat and vld should remain as output, while rdy should remain as input.
            # port_info["direction"] = "input" if port_info["direction"] == "output" else "output"
            
            port_name = f"{port.split('_rsc')[0]}_rsc{j}{suffix}"
            json_data["top_ports"][port_name] = port_info
    
    # Add result ports
    for port in port_groups["result"]:
        if port.endswith("_dat") or port.endswith("_vld") or port.endswith("_rdy"):
            # Create separate dat, vld, and rdy ports for each PE
            for k in range(rows * cols):
                port_info = create_port_copy(pe_ports[port])
                json_data["top_ports"][f"{port}{k}"] = port_info
    
    # Process instances
    # Look for array instances in the YAML
    for instance in config.get("instances", []):
        if "array" in instance:
            module_name = instance["module"]
            array_dims = instance["array"]
            array_rows, array_cols = array_dims[0], array_dims[1]
            
            # Create PE instances in the array
            for i in range(array_rows):
                for j in range(array_cols):
                    pe_name = f"PE_{i}_{j}"
                    json_data["instances"][pe_name] = {
                        "module": module_name,
                        "connect": {}
                    }
    
    # Process connections
    # Create internal wires for PE connections
    for i in range(rows):
        for j in range(cols):
            # Basic connections for all PEs
            for ctrl_port in control_ports:
                json_data["instances"][f"PE_{i}_{j}"]["connect"][ctrl_port] = ctrl_port
            
            # Skip rightmost column for horizontal connections
            if j < cols - 1:
                # Horizontal connections (right to left)
                for port in port_groups["right"]:
                    suffix = port.split("_rsc")[1] if "_rsc" in port else ""
                    
                    if suffix == "_dat":
                        wire_name = f"data_PE_{i}_{j}_to_PE_{i}_{j+1}"
                    elif suffix == "_vld":
                        wire_name = f"val_PE_{i}_{j}_to_PE_{i}_{j+1}"
                    elif suffix == "_rdy":
                        wire_name = f"rdy_PE_{i}_{j}_to_PE_{i}_{j+1}"
                    else:
                        wire_name = f"{port}_PE_{i}_{j}_to_PE_{i}_{j+1}"
                    
                    json_data["instances"][f"PE_{i}_{j}"]["connect"][port] = wire_name
                
                # Connect to the left inputs of the next PE
                for port in port_groups["left"]:
                    suffix = port.split("_rsc")[1] if "_rsc" in port else ""
                    
                    if suffix == "_dat":
                        wire_name = f"data_PE_{i}_{j}_to_PE_{i}_{j+1}"
                    elif suffix == "_vld":
                        wire_name = f"val_PE_{i}_{j}_to_PE_{i}_{j+1}"
                    elif suffix == "_rdy":
                        wire_name = f"rdy_PE_{i}_{j}_to_PE_{i}_{j+1}"
                    else:
                        wire_name = f"{port}_PE_{i}_{j}_to_PE_{i}_{j+1}"
                    
                    json_data["instances"][f"PE_{i}_{j+1}"]["connect"][port] = wire_name
            else:
                # Right edge
                for port in port_groups["right"]:
                    suffix = port.split("_rsc")[1] if "_rsc" in port else ""
                    prefix = port.split("_rsc")[0] if "_rsc" in port else port
                    top_port_name = f"{prefix}_rsc{i}{suffix}"
                    json_data["instances"][f"PE_{i}_{j}"]["connect"][port] = top_port_name
            
            # Skip bottom row for vertical connections
            if i < rows - 1:
                # Vertical connections (down to up)
                for port in port_groups["down"]:
                    suffix = port.split("_rsc")[1] if "_rsc" in port else ""
                    
                    if suffix == "_dat":
                        wire_name = f"data_PE_{i}_{j}_to_PE_{i+1}_{j}"
                    elif suffix == "_vld":
                        wire_name = f"val_PE_{i}_{j}_to_PE_{i+1}_{j}"
                    elif suffix == "_rdy":
                        wire_name = f"rdy_PE_{i}_{j}_to_PE_{i+1}_{j}"
                    else:
                        wire_name = f"{port}_PE_{i}_{j}_to_PE_{i+1}_{j}"
                    
                    json_data["instances"][f"PE_{i}_{j}"]["connect"][port] = wire_name
                
                # Connect to the up inputs of the PE below
                for port in port_groups["up"]:
                    suffix = port.split("_rsc")[1] if "_rsc" in port else ""
                    
                    if suffix == "_dat":
                        wire_name = f"data_PE_{i}_{j}_to_PE_{i+1}_{j}"
                    elif suffix == "_vld":
                        wire_name = f"val_PE_{i}_{j}_to_PE_{i+1}_{j}"
                    elif suffix == "_rdy":
                        wire_name = f"rdy_PE_{i}_{j}_to_PE_{i+1}_{j}"
                    else:
                        wire_name = f"{port}_PE_{i}_{j}_to_PE_{i+1}_{j}"
                    
                    json_data["instances"][f"PE_{i+1}_{j}"]["connect"][port] = wire_name
            else:
                # Bottom edge
                for port in port_groups["down"]:
                    suffix = port.split("_rsc")[1] if "_rsc" in port else ""
                    prefix = port.split("_rsc")[0] if "_rsc" in port else port
                    top_port_name = f"{prefix}_rsc{j}{suffix}"
                    json_data["instances"][f"PE_{i}_{j}"]["connect"][port] = top_port_name
            
            # Left edge
            if j == 0:
                for port in port_groups["left"]:
                    suffix = port.split("_rsc")[1] if "_rsc" in port else ""
                    prefix = port.split("_rsc")[0] if "_rsc" in port else port
                    top_port_name = f"{prefix}_rsc{i}{suffix}"
                    json_data["instances"][f"PE_{i}_{j}"]["connect"][port] = top_port_name
            
            # Top edge
            if i == 0:
                for port in port_groups["up"]:
                    suffix = port.split("_rsc")[1] if "_rsc" in port else ""
                    prefix = port.split("_rsc")[0] if "_rsc" in port else port
                    top_port_name = f"{prefix}_rsc{j}{suffix}"
                    json_data["instances"][f"PE_{i}_{j}"]["connect"][port] = top_port_name
            
            # Add result connections - Use the PE index to connect to the corresponding top-level port.
            pe_index = i * cols + j
            for port in port_groups["result"]:
                if port.endswith("_dat"):
                    json_data["instances"][f"PE_{i}_{j}"]["connect"][port] = f"{port}{pe_index}"
                elif port.endswith("_vld"):
                    json_data["instances"][f"PE_{i}_{j}"]["connect"][port] = f"{port}{pe_index}"
                elif port.endswith("_rdy"):
                    json_data["instances"][f"PE_{i}_{j}"]["connect"][port] = f"{port}{pe_index}"
    
    # Ensure that the target directory exists.
    os.makedirs(os.path.dirname(json_file), exist_ok=True)
    
    # Write JSON output
    with open(json_file, 'w') as f:
        json.dump(json_data, f, indent=2)
    
    print(f"Generated {json_file} successfully!")

if __name__ == "__main__":
    # Get the directory where the script is located.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set the project root directory (assuming the script is located in the scripts directory).
    project_root = os.path.dirname(script_dir)
    
    # Default parameters – adapted to the new file path structure.
    yaml_file = os.path.join(project_root, "src", "systolic_array.yaml")
    pe_config_file = os.path.join(project_root, "build", "submodule_pe_config.json")
    json_file = os.path.join(project_root, "build", "systolic_array_standard.json")
    
    # Check command-line arguments.
    if len(sys.argv) > 1:
        yaml_file = sys.argv[1]
    if len(sys.argv) > 2:
        pe_config_file = sys.argv[2]
    if len(sys.argv) > 3:
        json_file = sys.argv[3]
    
    # Check if the file exists.
    if not os.path.exists(yaml_file):
        print(f"Error: YAML configuration file does not exist: {yaml_file}")
        sys.exit(1)
    
    if not os.path.exists(pe_config_file):
        print(f"Error: PE configuration file does not exist: {pe_config_file}")
        sys.exit(1)
    
    # Generate the JSON file.
    generate_systolic_array_json(yaml_file, pe_config_file, json_file) 