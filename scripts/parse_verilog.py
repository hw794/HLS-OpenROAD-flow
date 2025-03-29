import re
import json
import os

SRC_DIR = "../src"
OUT_DIR = "../intermediate"

def parse_verilog(file_path):
    """Parse a Verilog file to extract module ports and their directions."""
    modules = {}

    with open(file_path, "r") as f:
        verilog_code = f.read()

    module_pattern = re.compile(r"module\s+(\w+)\s*\((.*?)\);", re.DOTALL)
    port_pattern = re.compile(r"(input|output)\s*(?:logic\s*)?(\[\d+:\d+\])?\s*(\w+)")

    internal_port_pattern = re.compile(r"(input|output)\s*(?:logic\s*)?(\[\d+:\d+\])?\s*(\w+)\s*;", re.MULTILINE)

    for match in module_pattern.finditer(verilog_code):
        module_name = match.group(1)
        module_ports = {}

        # Extract ports from the module declaration
        for port_match in port_pattern.finditer(match.group(2)):
            direction = port_match.group(1)
            width = port_match.group(2)
            port_name = port_match.group(3)

            module_ports[port_name] = {
                "direction": direction,
                "type": "logic",
                "width": int(width[1:-1].split(":")[0]) + 1 if width else 1
            }

        # Extract internal ports
        module_start = verilog_code.find(f"module {module_name}") + len(f"module {module_name}")
        module_body = verilog_code[module_start:]

        for port_match in internal_port_pattern.finditer(module_body):
            direction = port_match.group(1)
            width = port_match.group(2)
            port_name = port_match.group(3)

            if port_name not in module_ports:
                module_ports[port_name] = {
                    "direction": direction,
                    "type": "logic",
                    "width": int(width[1:-1].split(":")[0]) + 1 if width else 1
                }

        modules[module_name] = module_ports

    return modules


def generate_submodule_configs(verilog_files):
    parsed_modules = {}
    for v_file in verilog_files:
        parsed_modules.update(parse_verilog(os.path.join(SRC_DIR, v_file)))

    for module_name, ports in parsed_modules.items():
        module_config = {
            "submodule": module_name,
            "ports": ports
        }

        filename = os.path.join(OUT_DIR, f"module_{module_name.lower()}_config.json")
        with open(filename, "w") as json_file:
            json.dump(module_config, json_file, indent=2)
        print(f" Saved {filename}")

# Example Usage
# verilog_files = ["counter6.v", "counter10.v"]
verilog_files = ["PE.v"]
generate_submodule_configs(verilog_files)