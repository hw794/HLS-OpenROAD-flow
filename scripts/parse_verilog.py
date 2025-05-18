import re
import json
import os

SRC_DIR = "../src"
OUT_DIR = "../build"
SETUP_FILE = "../setup.json"

def parse_verilog(file_path):
    """
        Parse a Verilog file to extract the port information of each module.
        To avoid interference from the contents of other modules, use regular 
        expressions to capture the section from `module` to the corresponding `endmodule`.

    """
    modules = {}

    with open(file_path, "r") as f:
        verilog_code = f.read()

    # Modified module regex: capture the module name, the header (port list), and the module body (up to `endmodule`).
    module_pattern = re.compile(r"module\s+(\w+)\s*\((.*?)\);\s*(.*?)endmodule", re.DOTALL)
    # Capture port declarations: direction + optional type (`logic` | `wire` | `reg`) + optional bit width + port name.
    port_pattern = re.compile(r"(input|output)\s*(?:(logic|wire|reg)\s*)?(\[\d+:\d+\])?\s*(\w+)")
    # Must start with `input` or `output` in internal declarations.
    internal_port_pattern = re.compile(r"(input|output)\s*(?:(logic|wire|reg)\s*)?(\[\d+:\d+\])?\s*(\w+)\s*;", re.MULTILINE)
    # Standalone `reg` declarations (without `input`/`output`) are used to update the port type.
    reg_pattern = re.compile(r"reg\s*(\[\d+:\d+\])?\s*(\w+)\s*;")

    for match in module_pattern.finditer(verilog_code):
        module_name = match.group(1)
        header = match.group(2)
        body = match.group(3)
        module_ports = {}

        # First attempt to parse the ports in the header (which usually only contains port names).
        # If the header does not contain direction or other information, it may not match anything here.
        for port_match in port_pattern.finditer(header):
            direction = port_match.group(1)
            type_token = port_match.group(2)
            width = port_match.group(3)
            port_name = port_match.group(4)
            port_type = "reg" if type_token and type_token.strip() == "reg" else "wire"
            module_ports[port_name] = {
                "direction": direction,
                "type": port_type,
                "width": int(width[1:-1].split(":")[0]) + 1 if width else 1
            }

        # Parse port declarations in the module body.
        for port_match in internal_port_pattern.finditer(body):
            direction = port_match.group(1)
            type_token = port_match.group(2)
            width = port_match.group(3)
            port_name = port_match.group(4)
            port_type = "reg" if type_token and type_token.strip() == "reg" else "wire"
            # If already present, update the type to reg when applicable.
            if port_name in module_ports:
                if type_token and type_token.strip() == "reg":
                    module_ports[port_name]["type"] = "reg"
            else:
                module_ports[port_name] = {
                    "direction": direction,
                    "type": port_type,
                    "width": int(width[1:-1].split(":")[0]) + 1 if width else 1
                }
        # For declarations that start with reg alone, use reg_pattern to update the type of existing ports to reg.
        for reg_match in reg_pattern.finditer(body):
            width = reg_match.group(1)
            port_name = reg_match.group(2)
            if port_name in module_ports:
                module_ports[port_name]["type"] = "reg"

        modules[module_name] = module_ports

    return modules

################################################################################
# The following section is used to parse setup.json and generate the top-level 
# submodule configuration (named submodule_<top_submodule>_config.json).
################################################################################

def parse_setup_file(file_path):
    """
    Parse the setup.json file to extract the following information:

    -top_submodule: the name of the top-level submodule that forms the final top module
    -submodules: the list of Verilog files to be processed
    """
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return None, []

    with open(file_path, "r") as f:
        setup_data = json.load(f)
    
    # Retrieve the configuration from generate_files.
    generate_files = setup_data.get("generate_files", [])
    if not generate_files:
        print(f"Error: 'generate_files' section missing or empty in {file_path}")
        return None, []

    # Use the first configuration item (can be adjusted as needed).
    config = generate_files[0]
    top_submodule = config.get("top_submodule")
    submodule_name = config.get("submodules")
    
    # Append .v suffix if it has not already been added.
    verilog_file = f"{submodule_name}.v" if not submodule_name.endswith(".v") else submodule_name
    
    return top_submodule, [verilog_file]

def generate_submodule_configs(verilog_files, top_submodule):
    parsed_modules = {}
    for v_file in verilog_files:
        try:
            parsed_modules.update(parse_verilog(os.path.join(SRC_DIR, v_file)))
        except FileNotFoundError:
            print(f"Warning: Verilog file {v_file} not found in {SRC_DIR}")
            continue
    
    if not top_submodule:
        print("Error: top_submodule not specified in setup.json")
        return

    if top_submodule not in parsed_modules:
        print(f"Error: Top-level submodule '{top_submodule}' not found in parsed Verilog files.")
        return

    ports = parsed_modules[top_submodule]
    module_config = {
        "submodule": top_submodule,
        "ports": ports
    }

    # Generate the standard configuration file.
    filename = os.path.join(OUT_DIR, f"submodule_{top_submodule}_config.json")
    with open(filename, "w") as json_file:
        json.dump(module_config, json_file, indent=2)
    print(f"Saved {filename}")

# Main flow: parse setup.json, output the top-level submodule and the list of files to process, 
# then generate the configuration file.
# Ensure that OUT_DIR exists.
os.makedirs(OUT_DIR, exist_ok=True)

top_submodule, verilog_files = parse_setup_file(SETUP_FILE)
print("Top-level submodule:", top_submodule)
print("Verilog files to process:", verilog_files)

if top_submodule and verilog_files:
    generate_submodule_configs(verilog_files, top_submodule)
else:
    print("Error: Failed to extract necessary information from setup.json")