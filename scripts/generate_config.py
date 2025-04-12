import json
import os

SRC_DIR = "../src"
OUT_DIR = "../build"

def generate_submodule_config(connection_json_file, submodule_files):
    """Generate connection_config.json based on Clock.json and submodule configs."""
    with open(os.path.join(SRC_DIR, connection_json_file), "r") as json_file:
        connection_config = json.load(json_file)

    # Extract top_module from connection_config.json
    if "top_module" not in connection_config:
        raise KeyError("Missing 'top_module' in connection_config.json")

    top_module = connection_config["top_module"]
    instances = connection_config["instances"]
    top_ports = connection_config["top_ports"]

    # Read submodule configs
    submodules = {}
    for file in submodule_files:
        with open(os.path.join(OUT_DIR, file), "r") as json_file:
            submodule_data = json.load(json_file)
            submodules[submodule_data["submodule"]] = submodule_data

    # Process Instances
    for instance_name, instance_data in instances.items():
        module_name = instance_data["module"]
        if module_name not in submodules:
            raise ValueError(f"Module '{module_name}' not found in submodule configs")

        module_config = submodules[module_name]
        instance_connect = instance_data.get("connect", {})
        internal_nets = {}
        exposed_ports = {}

        # Handle internal nets and exposed ports
        for port, port_info in module_config["ports"].items():
            if port in instance_connect:
                signal = instance_connect[port]
                if signal not in ["0", "1"]:  # Avoid constants
                    internal_nets[signal] = port_info
            elif port_info["direction"] == "input":
                exposed_ports[port] = port_info

        # Handle output_map
        output_map = instance_data.get("output_map", {})
        for port, mapping in output_map.items():
            if port in module_config["ports"]:
                exposed_ports[mapping["signal"]] = {
                    "direction": "output",
                    "type": "logic",
                    "width": mapping["width"]
                }

        # Save instance-specific configuration
        module_config.setdefault("instances", {})[instance_name] = {
            "ports": {port: instance_connect.get(port, port) for port in module_config["ports"]},
            "internal_nets": internal_nets,
            "exposed_ports": exposed_ports
        }

    # Write connection_config.json (including top_module)
    connection_config_out = {
        "top_module": top_module,
        "instances": instances,
        "top_ports": top_ports
    }
    with open(os.path.join(OUT_DIR, "topmodule_config.json"), "w") as json_file:
        json.dump(connection_config_out, json_file, indent=2)

    print("Saved topmodule_config.json")

def parse_setup_file(file_path):
    """
    setup.txt
        # config.mk
        PLATFORM = 
        DESIGN_NAME = 
        DESIGN_NICKNAME = 
        CORE_UTILIZATION = 
        PLACE_DENSITY = 

        # constraint.sdc
        clk_period = 

        # generate_files
        submodules = counter6, counter10
        connection = systolic_array
    """
    connection = None
    submodules = []
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return connection, submodules

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("submodules"):
                parts = line.split("=")
                if len(parts) < 2:
                    continue
                mods = parts[1].strip().split(",")
                for mod in mods:
                    mod_name = mod.strip()
                    if mod_name:
                        filename = f"module_{mod_name.lower()}_config.json"
                        submodules.append(filename)
            elif line.startswith("connection"):
                parts = line.split("=")
                if len(parts) < 2:
                    continue
                conn = parts[1].strip()
                if conn:
                    if not conn.endswith(".json"):
                        conn += ".json"
                    connection = conn
    return connection, submodules

SETUP_FILE = "../setup.txt"  
connection_json_file, submodule_files = parse_setup_file(SETUP_FILE)

print("Connection JSON file:", connection_json_file)
print("Submodule config files:", submodule_files)

generate_submodule_config(connection_json_file, submodule_files)