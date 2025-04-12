import re
import sys
import os

DEFAULTS = {
    "PLATFORM": "asap7",
    "CLK_PERIOD": "475",
    "CLK_IO_PCT": "0.2",
    "CORE_ASPECT_RATIO": "1.0",
    "CORE_MARGIN": "5"
}

VALID_PLATFORMS = {"asap7", "nangate45"}
BUILD_DIR = "../build"

def load_config_txt(file="../setup.txt"):
    raw_config = {}
    try:
        with open(file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Match lines like: export VAR = value OR VAR = value
                match = re.match(r'^(?:export\s+)?(\w+)\s*=\s*(.+)$', line)
                if match:
                    key, value = match.groups()
                    raw_config[key.strip()] = value.strip()
    except FileNotFoundError:
        print(f"[Error] {file} not found.")
        sys.exit(1)
    return raw_config

def validate_and_complete_config(raw):
    config = {}

    # PLATFORM
    platform = raw.get("PLATFORM", "").strip()
    if not platform:
        platform = DEFAULTS["PLATFORM"]
    if platform not in VALID_PLATFORMS:
        raise ValueError(f"Invalid PLATFORM '{platform}'. Must be 'asap7' or 'nangate45'.")
    config["PLATFORM"] = platform

    # DESIGN_NAME (required)
    design_name = raw.get("DESIGN_NAME", "").strip()
    if not design_name:
        raise ValueError("DESIGN_NAME is required.")
    config["DESIGN_NAME"] = design_name

    # DESIGN_NICKNAME (optional)
    design_nickname = raw.get("DESIGN_NICKNAME", "").strip()
    if not design_nickname:
        design_nickname = design_name
    config["DESIGN_NICKNAME"] = design_nickname

    # CORE_UTILIZATION
    try:
        core_util = float(raw.get("CORE_UTILIZATION", ""))
        if not (0 < core_util < 100):
            raise ValueError
    except ValueError:
        raise ValueError("CORE_UTILIZATION must be a number between 0 and 100 (exclusive).")
    config["CORE_UTILIZATION"] = str(core_util)

    # PLACE_DENSITY
    place_density_str = raw.get("PLACE_DENSITY", "")
    if not re.match(r"^0\.\d{1,2}$|^1\.00$", place_density_str):
        raise ValueError("PLACE_DENSITY must be a decimal between 0 and 1 with up to two digits after the decimal point.")
    config["PLACE_DENSITY"] = place_density_str

    # CLK_PERIOD
    clk_period = raw.get("clk_period", DEFAULTS["CLK_PERIOD"])
    try:
        float(clk_period)
    except ValueError:
        raise ValueError("clk_period must be a number.")
    config["CLK_PERIOD"] = clk_period

    # CLK_IO_PCT
    clk_io_pct = raw.get("clk_io_pct", DEFAULTS["CLK_IO_PCT"])
    if not re.match(r"^0\.\d{1,2}$|^1\.00$", clk_io_pct):
        raise ValueError("clk_io_pct must be a decimal between 0 and 1 with up to two digits after the decimal point.")
    config["CLK_IO_PCT"] = clk_io_pct

    # CORE_ASPECT_RATIO
    try:
        aspect_ratio = float(raw.get("CORE_ASPECT_RATIO", DEFAULTS["CORE_ASPECT_RATIO"]))
        if not (0.5 <= aspect_ratio <= 5):
            raise ValueError
    except ValueError:
        raise ValueError("CORE_ASPECT_RATIO must be a number between 0.5 and 5.")
    config["CORE_ASPECT_RATIO"] = str(aspect_ratio)

    # CORE_MARGIN
    try:
        core_margin = int(raw.get("CORE_MARGIN", DEFAULTS["CORE_MARGIN"]))
        if not (2 <= core_margin <= 20):
            raise ValueError
    except ValueError:
        raise ValueError("CORE_MARGIN must be an integer between 2 and 20.")
    config["CORE_MARGIN"] = str(core_margin)

    # VERILOG_FILES and SDC_FILE
    verilog_path = f"$(sort $(wildcard $(DESIGN_HOME)/src/{design_nickname}/*.v))"
    sdc_path = f"$(DESIGN_HOME)/{platform}/{design_nickname}/constraint.sdc"

    config["VERILOG_FILES"] = verilog_path
    config["SDC_FILE"] = sdc_path

    return config

def write_config_mk(config, filename=f"{BUILD_DIR}/config.mk"):
    os.makedirs(BUILD_DIR, exist_ok=True)
    with open(filename, "w") as f:
        f.write("# Auto-generated config.mk\n")
        for key in [
            "PLATFORM", "DESIGN_NAME", "DESIGN_NICKNAME", "CORE_UTILIZATION",
            "PLACE_DENSITY", "CORE_ASPECT_RATIO", "CORE_MARGIN",
            "VERILOG_FILES", "SDC_FILE"
        ]:
            f.write(f'export {key:<20} = {config[key]}\n')
    print(f"[Success] {filename} generated.")

def write_constraint_sdc(config, filename=f"{BUILD_DIR}/constraint.sdc"):
    os.makedirs(BUILD_DIR, exist_ok=True)
    with open(filename, "w") as f:
        f.write("# Auto-generated constraint.sdc\n\n")
        f.write("set clk_name       clk\n")
        f.write("set clk_port_name  clk\n")
        f.write(f"set clk_period     {config['CLK_PERIOD']}\n")
        f.write(f"set clk_io_pct     {config['CLK_IO_PCT']}\n\n")
        f.write("set clk_port [get_ports $clk_port_name]\n\n")
        f.write("create_clock -name $clk_name -period $clk_period $clk_port\n\n")
        f.write("set non_clock_inputs [lsearch -inline -all -not -exact [all_inputs] $clk_port]\n\n")
        f.write("set_input_delay  [expr $clk_period * $clk_io_pct] -clock $clk_name $non_clock_inputs\n")
        f.write("set_output_delay [expr $clk_period * $clk_io_pct] -clock $clk_name [all_outputs]\n")
    print(f"[Success] {filename} generated.")

def main():
    try:
        raw_config = load_config_txt()
        config = validate_and_complete_config(raw_config)
        write_config_mk(config)
        write_constraint_sdc(config)
    except Exception as e:
        print(f"[Error] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
