import json
import os

# Directory Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(SCRIPT_DIR, "../src")
OUT_DIR = os.path.join(SCRIPT_DIR, "../build")

def load_submodule_configs(submodule_files):
    """Load submodule JSON files into a dictionary keyed by module name (in lower-case)."""
    submodules = {}
    for file in submodule_files:
        file_path = os.path.join(OUT_DIR, file)
        with open(file_path, "r") as json_file:
            submodule_data = json.load(json_file)
            submodules[submodule_data["submodule"].lower()] = submodule_data["ports"]
    return submodules

def format_signal(direction, width, name):
    """Format signal declaration without 'logic', e.g., 'input [3:0] clk,'."""
    width_str = f"[{width-1}:0] " if width > 1 else ""
    return f"  {direction} {width_str}{name},"

def format_wire(width, name):
    """Format wire declaration with width."""
    width_str = f"[{width-1}:0] " if width > 1 else ""
    return f"  wire {width_str}{name};"

def generate_top_verilog(connection_config_file, submodule_files, design_name):
    """
    Generate top-level Verilog code based on connection_config.json and submodule configs.
    - connection_config_file is read from OUT_DIR.
    - submodule_files is a list of submodule configuration file names (located in OUT_DIR).
    - design_name is used for naming the generated top-level Verilog file.
    """
    # read connection JSON file
    with open(os.path.join(OUT_DIR, connection_config_file), "r") as json_file:
        connection_config = json.load(json_file)

    top_module = connection_config["top_module"]
    instances = connection_config["instances"]
    top_ports = connection_config["top_ports"]

    # read submodule ports
    submodule_ports = load_submodule_configs(submodule_files)

    port_definitions = []
    internal_wires = []

    # Generate top-level port declarations (directly based on connection_config's top_ports)
    for port_name, port_info in top_ports.items():
        port_definitions.append(format_signal(port_info["direction"], port_info["width"], port_name))

    # Process the connect field of each instance to generate internal wires (only for output ports)
    for instance_name, instance_data in instances.items():
        module_name = instance_data["module"].lower()  # 统一小写匹配
        module_ports = submodule_ports[module_name]

        # For output ports, if the signal in connect is not a constant and is not already defined as a top-level port, generate an internal wire.
        for port, signal in instance_data.get("connect", {}).items():
            if port in module_ports and module_ports[port]["direction"] == "output":
                # If the signal name appears in top_ports (top-level interfaces), it is considered directly connected externally, and no internal wire is needed.
                if signal in top_ports:
                    continue
                if signal not in ["0", "1"] and signal not in [wire.split(" ")[-1].strip(";") for wire in internal_wires]:
                    internal_wires.append(format_wire(module_ports[port]["width"], signal))

        # For output_map, map the corresponding output to the top-level interface.
        for port, mapping in instance_data.get("output_map", {}).items():
            if port in module_ports and module_ports[port]["direction"] == "output":
                if isinstance(mapping, dict):
                    mapped_signal = mapping["signal"]
                    mapped_width = mapping["width"]
                else:
                    mapped_signal = mapping
                    mapped_width = module_ports[port]["width"]
                port_definitions.append(format_signal("output", mapped_width, mapped_signal))

    # Assemble the top-level module code.
    verilog_code = f"// Auto-generated top module\nmodule {top_module}(\n"
    verilog_code += "\n".join(port_definitions).rstrip(",") + "\n);\n\n"

    if internal_wires:
        verilog_code += "// Internal nets\n" + "\n".join(internal_wires) + "\n\n"

    # Generate the instantiation code for each instance.
    for instance_name, instance_data in instances.items():
        module_name = instance_data["module"]
        module_ports = submodule_ports[module_name.lower()]
        verilog_code += f"  // Instance of {module_name}\n"
        verilog_code += f"  {module_name} {instance_name} (\n"

        port_connections = []
        for port, port_info in module_ports.items():
            if port in instance_data.get("connect", {}):
                mapped_signal = instance_data["connect"][port]
            elif port in instance_data.get("output_map", {}):
                mapping = instance_data["output_map"][port]
                mapped_signal = mapping["signal"] if isinstance(mapping, dict) else mapping
            else:
                mapped_signal = port
            port_connections.append(f"    .{port}({mapped_signal})")
        verilog_code += ",\n".join(port_connections) + "\n  );\n\n"

    verilog_code += "endmodule\n"

    # Write the final generated top-level Verilog to OUT_DIR, with the filename DESIGN_NAME.v.
    output_filename = os.path.join(OUT_DIR, f"{design_name}.v")
    with open(output_filename, "w") as verilog_file:
        verilog_file.write(verilog_code)

    print(f"Saved {design_name}.v")

def parse_setup_file(file_path):
    """
    Parse setup.json file to extract:
      - DESIGN_NAME: used for naming the generated top-level Verilog file.
      - connection: the connection JSON file.
      - top_submodule: the name of the top submodule to use.
    """
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return None, None, []

    with open(file_path, "r") as f:
        setup_data = json.load(f)
    
    # Retrieve DESIGN_NAME from config_mk.
    design_name = setup_data.get("config_mk", {}).get("DESIGN_NAME")
    
    # Retrieve configuration from generate_files.
    generate_files = setup_data.get("generate_files", [])
    if not generate_files:
        print(f"Error: 'generate_files' section missing or empty in {file_path}")
        return design_name, None, []

    # Use the first configuration item.
    config = generate_files[0]
    top_submodule = config.get("top_submodule")
    connection = config.get("connection")
    
    # Append .json suffix if it has not already been added.
    connection_file = f"{connection}.json" if connection and not connection.endswith(".json") else connection
    
    submodules = []
    if top_submodule:
        # The filename format for the top-level submodule configuration is "submodule_<top_submodule>_config.json".
        submodules.append(f"submodule_{top_submodule.lower()}_config.json")
    
    return design_name, connection_file, submodules

# Main flow
SETUP_FILE = os.path.join(SCRIPT_DIR, "../setup.json")
design_name, connection_config_file, submodule_files = parse_setup_file(SETUP_FILE)

print("DESIGN_NAME:", design_name)
print("Connection JSON file:", connection_config_file)
print("Submodule config files:", submodule_files)

if design_name and connection_config_file and submodule_files:
    generate_top_verilog(connection_config_file, submodule_files, design_name)
else:
    print("Error: Failed to extract necessary information from setup.json")