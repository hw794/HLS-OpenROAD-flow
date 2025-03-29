import json
import os

SRC_DIR = "../src"
OUT_DIR = "../intermediate"

def generate_submodule_config(clock_json_file, submodule_files):
    """Generate Clock_config.json based on Clock.json and submodule configs."""
    with open(os.path.join(SRC_DIR, clock_json_file), "r") as json_file:
        clock_config = json.load(json_file)

    #  Extract top_module from Clock.json
    if "top_module" not in clock_config:
        raise KeyError("Missing 'top_module' in Clock.json")

    top_module = clock_config["top_module"]
    instances = clock_config["instances"]
    top_ports = clock_config["top_ports"]

    #  Read submodule configs
    submodules = {}
    for file in submodule_files:
        with open(os.path.join(OUT_DIR, file), "r") as json_file:
            submodule_data = json.load(json_file)
            submodules[submodule_data["submodule"]] = submodule_data

    #  Process Instances
    for instance_name, instance_data in instances.items():
        module_name = instance_data["module"]
        if module_name not in submodules:
            raise ValueError(f"Module '{module_name}' not found in submodule configs")

        module_config = submodules[module_name]
        instance_connect = instance_data.get("connect", {})
        internal_nets = {}
        exposed_ports = {}

        #  Handle internal nets and exposed ports
        for port, port_info in module_config["ports"].items():
            if port in instance_connect:
                signal = instance_connect[port]
                if signal not in ["0", "1"]:  # Avoid constants
                    internal_nets[signal] = port_info
            elif port_info["direction"] == "input":
                exposed_ports[port] = port_info

        #  Handle output_map
        output_map = instance_data.get("output_map", {})
        for port, mapping in output_map.items():
            if port in module_config["ports"]:
                exposed_ports[mapping["signal"]] = {
                    "direction": "output",
                    "type": "logic",
                    "width": mapping["width"]
                }

        #  Save instance-specific configuration
        module_config.setdefault("instances", {})[instance_name] = {
            "ports": {port: instance_connect.get(port, port) for port in module_config["ports"]},
            "internal_nets": internal_nets,
            "exposed_ports": exposed_ports
        }

    #  Write Clock_config.json (including top_module)
    clock_config_out = {
        "top_module": top_module,
        "instances": instances,
        "top_ports": top_ports
    }
    with open(os.path.join(OUT_DIR, "topmodule_config.json"), "w") as json_file:
        json.dump(clock_config_out, json_file, indent=2)

    print("Saved topmodule_config.json")

# Example Usage
# clock_json_file = "Clock.json"
clock_json_file = "systolic_array.json"
# submodule_files = ["module_counter6_config.json", "module_counter10_config.json"]
submodule_files = ["module_pe_config.json"]
generate_submodule_config(clock_json_file, submodule_files)