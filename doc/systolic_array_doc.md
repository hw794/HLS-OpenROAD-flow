# Systolic Array YAML Configuration Guide

## Introduction

The `systolic_array.yaml` file is used to describe the structure and connections of a two-dimensional systolic array. With this configuration file, users can easily define the dimensions of the systolic array, the connections between internal processing elements, and external interfaces. **The configuration supports arbitrary NxM dimensions**, allowing users to create systolic arrays of any size based on their application requirements.

## Basic Structure of the Configuration File

```yaml
# Top-level module information
top_module: SystolicArray    # Top-level module name
dimensions: [2, 2]           # Array dimensions [rows, columns] - can be any size

# Top-level port definitions
top_ports:
  - name: clk                # Clock signal
    direction: input
    width: 1
  - name: rst                # Reset signal
    direction: input
    width: 1

# Instance configurations
instances:
  - name: C                  # Processing element instance name prefix
    module: pe               # Processing element module name
    array: [2, 2]            # Processing element array size - matches dimensions
    use_macro: true          # Use macro cell implementation

# Connection definitions
connections:
  # Example 1: Connect global signals to all PEs
  - for:                     # Loop definition for connections
      i: 2                   # Loop range i: 0~1
      j: 2                   # Loop range j: 0~1
    connect:                 # Regular signal connection
      signal: "clk"          # Source signal
      to: ["C-{i}_{j}.clk"]  # Target signal list
```

## Detailed Configuration Explanation

### Top-level Module Definition

- `top_module`: Specifies the name of the generated top-level module
- `dimensions`: Defines the dimensions of the systolic array in format `[rows, columns]` - can be any size according to your needs

### Top-level Port Definition

The `top_ports` section defines the input/output ports of the top-level systolic array module:

```yaml
top_ports:
  - name: port_name
    direction: input/output   # Direction: input or output
    width: bit_width          # Bit width, 1 for a single bit
```

### Instance Configuration

The `instances` section defines the processing element instances used in the systolic array:

```yaml
instances:
  - name: instance_prefix     # Generated instance names will be "prefix-row_col"
    module: module_name       # Corresponding Verilog module name
    array: [rows, columns]    # Array dimensions - should match top-level dimensions
    use_macro: true/false     # Whether to use macro cell implementation
```

### Connection Definition

The `connections` section defines the connections between processing elements in the systolic array:

#### Regular Signal Connection

```yaml
- for:                        # Define loop range
    i: rows                   # i will range from 0 to (rows-1)
    j: columns                # j will range from 0 to (columns-1)
  connect:                    # Regular signal connection
    signal: "signal_name"     # Source signal name
    to: ["target1", "target2"] # Target signal list, can use {i} and {j} to reference loop variables
```

#### Handshake Signal Connection

Handshake signals typically include data, valid, and ready signals for data transfer between processing elements:

```yaml
- for:
    i: rows
    j: columns
  connect_handshake:          # Handshake signal connection
    from: "source_handshake"  # Source handshake interface
    to: "target_handshake"    # Target handshake interface
```

## Example: 2x2 Systolic Array Configuration

Below is the 2x2 systolic array configuration example you provided, which uses left/right and up/down direction naming instead of the traditional east/west and north/south:

```yaml
# Systolic Array Configuration
top_module: SystolicArray
dimensions: [2, 2]  # 2x2 array

# Top-level ports
top_ports:
  - name: clk
    direction: input
    width: 1
  - name: rst
    direction: input
    width: 1

# Instance configurations
instances:
  - name: C
    module: pe
    array: [2, 2]
    use_macro: true

# Connections
connections:
  # Connect clock and reset to all PEs
  - for: 
      i: 2
      j: 2
    connect: 
      signal: "clk"
      to: ["C-{i}_{j}.clk"]
  - for:
      i: 2
      j: 2
    connect:
      signal: "rst"
      to: ["C-{i}_{j}.rst"]
      
  # Data flow between PEs (horizontal direction)
  - for:
      i: 2
      j: 1  # Only j=0 PEs need connection to j+1
    connect_handshake:
      from: "C-{i}_{j}.right"
      to: "C-{i}_{j+1}.left"
      
  # Data flow between PEs (vertical direction)
  - for:
      i: 1  # Only i=0 PEs need connection to i+1
      j: 2
    connect_handshake:
      from: "C-{i}_{j}.down"
      to: "C-{i+1}_{j}.up"
      
  # Connect input data to leftmost PE column
  - for:
      i: 2
      j: 0  # j=0 column (leftmost)
    connect_handshake:
      from: "left_in_{i}"
      to: "C-{i}_{j}.left"
      
  # Connect input data to topmost PE row
  - for:
      i: 0  # i=0 row (topmost)
      j: 2
    connect_handshake:
      from: "up_in_{j}"
      to: "C-{i}_{j}.up"
      
  # Connect output data from rightmost column
  - for:
      i: 2
      j: 1  # j=1 column (rightmost)
    connect_handshake:
      from: "C-{i}_{j}.right"
      to: "right_out_{i}"
      
  # Connect output data from bottom row
  - for:
      i: 1  # i=1 row (bottom)
      j: 2
    connect_handshake:
      from: "C-{i}_{j}.down"
      to: "down_out_{j}"
      
  # Connect result ready signals
  - for:
      i: 2
      j: 2
    connect:
      signal: "result_out_rsc_rdy{i*2+j}"
      to: ["C-{i}_{j}.result_out_rsc_rdy"]
```

## Extending to Larger Arrays

The configuration can be easily extended to larger arrays by changing the dimensions and updating the connection patterns. For example, to create a 4x4 array:

1. Set `dimensions: [4, 4]` in the top-level
2. Update `array: [4, 4]` in the instances section
3. Use `i: 4` and `j: 4` in the connection loops
4. Keep the same connection patterns, which will automatically scale to the larger array

## Important Notes

1. **Loop Ranges**: In the configuration file, a loop range `i: N` means i will range from 0 to N-1, so for a 2x2 array, use `i: 2` and `j: 2`

2. **Boundary Elements**: When connecting horizontal and vertical data flows, special attention is needed for boundary elements:
   - For horizontal connections (right/left), only connections from j=0 to j=1 need to be handled
   - For vertical connections (up/down), only connections from i=0 to i=1 need to be handled

3. **Direction Naming**: This configuration uses left/right and up/down as direction naming instead of the traditional east/west and north/south

4. **Macro Cell Support**: The configuration supports the `use_macro: true` option, allowing the use of predefined macro cells for implementing processing elements

5. **Custom Result Ready Signals**: Unique result ready signals are assigned to each processing element using the formula `{i*2+j}`
