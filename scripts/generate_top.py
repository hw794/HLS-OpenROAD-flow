import json
import os

# Directory Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, "../src")
OUT_DIR = os.path.join(SCRIPT_DIR, "../build")

def load_submodule_configs(submodule_files):
    """Load submodule JSON files into a dictionary."""
    submodules = {}
    for file in submodule_files:
        with open(os.path.join(OUT_DIR, file), "r") as json_file:
            submodule_data = json.load(json_file)
            submodules[submodule_data["submodule"]] = submodule_data["ports"]
    return submodules

def format_signal(direction, width, name):
    """Format signal declarations based on width."""
    width_str = f"[{width-1}:0] " if width > 1 else ""
    return f"  {direction} logic {width_str}{name},"

def format_wire(width, name):
    """Format wire declarations."""
    width_str = f"[{width-1}:0] " if width > 1 else ""
    return f"  wire {width_str}{name};"

def generate_top_verilog(connection_config_file, submodule_files, design_name):
    """Generate top-level Verilog code based on connection_config.json and submodule configs."""
    
    with open(os.path.join(SRC_DIR, connection_config_file), "r") as json_file:
        connection_config = json.load(json_file)

    top_module = connection_config["top_module"]
    instances = connection_config["instances"]
    top_ports = connection_config["top_ports"]

    # Read submodule JSON files from OUT_DIR
    submodule_ports = load_submodule_configs(submodule_files)

    # Ports and Connections
    port_definitions = []
    internal_wires = []

    # Handle top-level ports (input & output)
    for port_name, port_info in top_ports.items():
        port_definitions.append(format_signal(port_info["direction"], port_info["width"], port_name))

    # Handle instance ports connection
    for instance_name, instance_data in instances.items():
        module_name = instance_data["module"]
        module_ports = submodule_ports[module_name]

        # Handle `connect` -> generate internal `wire`
        for port, signal in instance_data.get("connect", {}).items():
            if port in module_ports and module_ports[port]["direction"] == "output":
                # Avoid declaring constants as wires
                if signal not in ["0", "1"] and signal not in [wire.split(" ")[-1].strip(";") for wire in internal_wires]:
                    internal_wires.append(format_wire(module_ports[port]["width"], signal))

        # Handle `output_map` to connect output ports to top-level ports
        for port, mapping in instance_data.get("output_map", {}).items():
            if port in module_ports and module_ports[port]["direction"] == "output":
                port_definitions.append(format_signal("output", mapping["width"], mapping["signal"]))

    # Generate Verilog Code
    verilog_code = f"// Auto-generated top module\nmodule {top_module}(\n"
    verilog_code += "\n".join(port_definitions).rstrip(",") + "\n);\n\n"

    # Add wire connections (skip width if [0:0])
    if internal_wires:
        verilog_code += "// Internal nets\n" + "\n".join(internal_wires) + "\n\n"

    # Instantiate all submodules
    for instance_name, instance_data in instances.items():
        module_name = instance_data["module"]
        module_ports = submodule_ports[module_name]

        verilog_code += f"  // Instance of {module_name}\n"
        verilog_code += f"  {module_name} {instance_name} (\n"

        # Ports mapping
        port_connections = []
        for port, port_info in module_ports.items():
            if port in instance_data.get("connect", {}):
                mapped_signal = instance_data["connect"][port]
            elif port in instance_data.get("output_map", {}):
                mapped_signal = instance_data["output_map"][port]["signal"]
            else:
                mapped_signal = port

            port_connections.append(f"    .{port}({mapped_signal})")

        verilog_code += ",\n".join(port_connections) + "\n  );\n\n"

    verilog_code += "endmodule\n"

    # Write Verilog File into build folder, file name is DESIGN_NAME.v
    with open(os.path.join(OUT_DIR, f"{design_name}.v"), "w") as verilog_file:
        verilog_file.write(verilog_code)

    print(f"Saved {design_name}.v")

def parse_setup_file(file_path):
    """
    setup.txt
        # config.mk
        PLATFORM = 
        DESIGN_NAME = SystolicArray
        DESIGN_NICKNAME = 
        CORE_UTILIZATION = 
        PLACE_DENSITY = 

        # constraint.sdc
        clk_period = 

        # generate_files
        submodules = pe
        connection = systolic_array
    """
    design_name = None
    connection = None
    submodules = []
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return design_name, connection, submodules

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("design_name"):
                parts = line.split("=")
                if len(parts) >= 2:
                    design_name = parts[1].strip()
            elif line.lower().startswith("submodules"):
                parts = line.split("=")
                if len(parts) >= 2:
                    mods = parts[1].strip().split(",")
                    for mod in mods:
                        mod_name = mod.strip()
                        if mod_name:
                            filename = f"module_{mod_name.lower()}_config.json"
                            submodules.append(filename)
            elif line.lower().startswith("connection"):
                parts = line.split("=")
                if len(parts) >= 2:
                    conn = parts[1].strip()
                    if conn and not conn.endswith(".json"):
                        conn += ".json"
                    connection = conn
    return design_name, connection, submodules

SETUP_FILE = os.path.join(SCRIPT_DIR, "../setup.txt")  
design_name, connection_config_file, submodule_files = parse_setup_file(SETUP_FILE)

print("DESIGN_NAME:", design_name)
print("Connection JSON file:", connection_config_file)
print("Submodule config files:", submodule_files)

generate_top_verilog(connection_config_file, submodule_files, design_name)