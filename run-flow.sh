#!/bin/bash

# Exit on error
set -e

# Create build directory
mkdir -p build

# Run Python scripts in order
cd scripts
python3 setup_configmk.py
python3 parse_verilog.py
python3 generate_config.py
python3 generate_top.py
cd ..

# Parse setup.txt for PLATFORM and DESIGN_NICKNAME
SETUP_FILE="setup.txt"

# Extract values using grep and awk
PLATFORM=$(grep "^PLATFORM" "$SETUP_FILE" | awk -F ' = ' '{print $2}')
DESIGNNAME=$(grep "^DESIGN_NAME" "$SETUP_FILE" | awk -F ' = ' '{print $2}')
NICKNAME=$(grep "^DESIGN_NICKNAME" "$SETUP_FILE" | awk -F ' = ' '{print $2}')

# Sanity check
if [[ -z "$PLATFORM" || -z "$NICKNAME" ]]; then
  echo "Error: PLATFORM or DESIGN_NICKNAME not found in $SETUP_FILE"
  exit 1
fi

# Create the design directory
mkdir -p "../designs/$PLATFORM/$NICKNAME"
cp build/config.mk ../designs/$PLATFORM/$NICKNAME/config.mk
cp build/constraint.sdc ../designs/$PLATFORM/$NICKNAME/constraint.sdc

mkdir -p "../designs/src/$NICKNAME"
cp build/$DESIGNNAME.v ../designs/src/$NICKNAME/$DESIGNNAME.v
cp src/*.v ../designs/src/$NICKNAME/

cd ..
source ../env.sh
make clean_all DESIGN_CONFIG=designs/$PLATFORM/$NICKNAME/config.mk
make DESIGN_CONFIG=designs/$PLATFORM/$NICKNAME/config.mk


