import json
import os

# Ensure build directory exists
os.makedirs('../build', exist_ok=True)

# Load setup.json
with open('../setup.json', 'r') as f:
    setup = json.load(f)

# Extract configuration sections
config = setup["config_mk"]
platform = config["PLATFORM"]
design_name = config["DESIGN_NAME"]
design_nickname = config["DESIGN_NICKNAME"]

constraint_sdc = setup.get("constraint_sdc", {})
macro_cfg = setup.get("macro_config", {})
manual_area_cfg = setup.get("manual_area_config", {})
generate_files = setup.get("generate_files", [])

# Flags
macro_enabled = macro_cfg.get("enable", False)
macro_add_annealing = macro_cfg.get("add_place_pins_args", False)
top_add_annealing = setup.get("add_place_pins_args", False)
manual_area_enabled = manual_area_cfg.get("enable", False)

# -----------------------------------------------------------------------------
# Write to config.mk
# -----------------------------------------------------------------------------

with open('../build/config.mk', 'w') as f:
    for key, value in config.items():
        if manual_area_enabled and key == "CORE_UTILIZATION":
            continue  # Skip writing CORE_UTILIZATION if manual area is enabled
        f.write(f"export {key} = {value}\n")

    if manual_area_enabled:
        die_area = manual_area_cfg.get("DIE_AREA", [])
        core_area = manual_area_cfg.get("CORE_AREA", [])
        if len(die_area) == 4:
            f.write(f"export DIE_AREA  = {' '.join(map(str, die_area))}\n")
        if len(core_area) == 4:
            f.write(f"export CORE_AREA = {' '.join(map(str, core_area))}\n")

    if top_add_annealing or macro_add_annealing:
        f.write("export PLACE_PINS_ARGS = -annealing\n")

    if macro_enabled:
        f.write(f"export BLOCKS ?= {macro_cfg['macro_names']}\n")
        f.write("export SYNTH_HIERARCHICAL = 1\n")

    f.write(f"export VERILOG_FILES = $(sort $(wildcard ./designs/src/{design_nickname}/*.v))\n")
    f.write(f"export SDC_FILE      = ./designs/{platform}/{design_nickname}/constraint.sdc\n")
    f.write(f"export GND_NETS_VOLTAGES      =\n")
    f.write(f"export PWR_NETS_VOLTAGES      =\n")

# -----------------------------------------------------------------------------
# Write to constraint.sdc
# -----------------------------------------------------------------------------

with open('../build/constraint.sdc', 'w') as f:
    clk_period = constraint_sdc.get("clk_period", 475)
    clk_io_pct = constraint_sdc.get("clk_io_pct", 0.3)
    f.write("set clk_name  clk\n")
    f.write("set clk_port_name clk\n")
    f.write(f"set clk_period {clk_period}\n")
    f.write(f"set clk_io_pct {clk_io_pct}\n\n")
    f.write("set clk_port [get_ports $clk_port_name]\n\n")
    f.write("create_clock -name $clk_name -period $clk_period $clk_port\n\n")
    f.write("set non_clock_inputs [lsearch -inline -all -not -exact [all_inputs] $clk_port]\n\n")
    f.write("set_input_delay  [expr $clk_period * $clk_io_pct] -clock $clk_name $non_clock_inputs\n")
    f.write("set_output_delay [expr $clk_period * $clk_io_pct] -clock $clk_name [all_outputs]\n")

# -----------------------------------------------------------------------------
# Write to generate_files
# -----------------------------------------------------------------------------

with open('../build/generate_files', 'w') as f:
    for entry in generate_files:
        f.write(f"submodules = {entry['submodules']}\n")
        f.write(f"connection = {entry['connection']}\n")
        if 'top_submodule' in entry:
            f.write(f"top_submodule = {entry['top_submodule']}\n")

# -----------------------------------------------------------------------------
# Conditionally write block.mk (only if macro_enabled)
# -----------------------------------------------------------------------------

if macro_enabled:
    with open('../build/block.mk', 'w') as f:
        f.write(f"export PLATFORM = {macro_cfg['PLATFORM']}\n")
        f.write(f"export CORE_UTILIZATION = {macro_cfg['CORE_UTILIZATION']}\n")  # Always keep this in block.mk
        f.write(f"export CORE_ASPECT_RATIO = {macro_cfg['CORE_ASPECT_RATIO']}\n")
        f.write(f"export CORE_MARGIN = {macro_cfg['CORE_MARGIN']}\n")
        f.write(f"export PLACE_DENSITY = {macro_cfg['PLACE_DENSITY']}\n")
        if macro_add_annealing:
            f.write("export PLACE_PINS_ARGS = -annealing\n")
        f.write(f"export VERILOG_FILES = $(sort $(wildcard ./designs/src/{design_nickname}/*.v))\n")
        f.write(f"export SDC_FILE      = ./designs/{platform}/{design_nickname}/constraint.sdc\n")
