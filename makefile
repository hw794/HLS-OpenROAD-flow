# Directories
SRC_DIR = src
SCRIPT_DIR = scripts
INTERMEDIATE_DIR = intermediate

# Generated files
GENERATED_FILES = Topmodule.v $(INTERMEDIATE_DIR)/module_pe_config.json $(INTERMEDIATE_DIR)/topmodule_config.json

# Default target
all: $(GENERATED_FILES)

# Parse Verilog files and generate module configs
$(INTERMEDIATE_DIR)/module_pe_config.json: $(SRC_DIR)/PE.v $(SCRIPT_DIR)/parse_verilog.py
	cd $(SCRIPT_DIR) && python3 parse_verilog.py

# Generate submodule config
$(INTERMEDIATE_DIR)/topmodule_config.json: $(SCRIPT_DIR)/generate_config.py $(SRC_DIR)/systolic_array.json $(INTERMEDIATE_DIR)/module_pe_config.json
	cd $(SCRIPT_DIR) && python3 generate_config.py

# Generate top module Verilog
Topmodule.v: $(SCRIPT_DIR)/generate_top.py $(INTERMEDIATE_DIR)/topmodule_config.json $(INTERMEDIATE_DIR)/module_pe_config.json
	cd $(SCRIPT_DIR) && python3 generate_top.py

# Clean generated files
clean:
	rm -f $(GENERATED_FILES) $(INTERMEDIATE_DIR)/*

# Force rebuild
rebuild: clean all

.PHONY: all clean rebuild