# HLS-OpenROAD-flow
This is a Cornell ECE M.Eng. project that aims to automate the ASIC design flow, allowing users to generate the physical design of their circuits with minimal effort. The project focuses on taking existing HLS-based RTL designs and automatically generating the physical layout.

To complete this project, we need to develop an end-to-end configuration that automates the tool flow from HLS (High-Level Synthesis) to ASIC layout. The deliverables will enable users to perform ASIC design using HLS and generate chip layouts more efficiently.

These deliverables will allow users to seamlessly convert their high-level designs into manufacturable physical layouts, ultimately enhancing chip design efficiency and lowering the barrier for developers who lack expertise in traditional hardware description and physical design.

Introduction
As mentioned in the previous section, our goal for this project is to develop an end-to-end configuration flow to automate and optimize the process of generating ASIC physical layouts directly from HLS-based RTL designs. Establishing such a flow will be remarkable because it will make it significantly easier for developers to perform ASIC or accelerator design and generate a GDSII file (a binary database file format that is an industry standard for IC layout design) that can be used to manufacture the chip. Developers will now be able to physically implement their designs using high-level programming languages (e.g., C++) with minimal knowledge or background in hardware description languages (e.g., SystemVerilog, Verilog, VHDL). This will lower the barrier to IC design in general, enabling researchers from different fields to achieve a more efficient design implementation flow.

Background
The field of ASIC design traditionally requires a deep understanding of hardware description languages (HDLs) such as Verilog or VHDL. However, high-level synthesis (HLS) tools allow software engineers to design hardware using high-level programming languages such as C++. While HLS tools like Catapult can generate RTL code from C++, the conversion of this RTL intoa physical layout for manufacturing has not been fully automated. Currently, there is no unified toolchain that allows users to automatically convert an HLS-based design to a physical ASIC layout with minimal manual intervention. The absence of such a toolchain limits the potential for rapid hardware design and prototyping, particularly for applications like sparse linear algebra 
accelerators.

Problem Statement
There is currently no single tool that can achieve this goal. Therefore, our primary challenge will be determining how to utilize different tools and design a tool flow that meets our design requirements. Another key challenge is that digital RTL design does not specify any physical constraints for manufacturing, as it is developed at a high level with a primary focus on functionality, without providing a method for specifying physical layout constraints such as area,timing, and power which are crucial for the final chip design.Consequently, we need to identify the appropriate stage for users to input physical constraints for the design, enabling the physical design tool to perform layout floorplanning and routing properly.

Approach and Expected Results
We plan to use Catapult HLS to synthesize C++ into RTL code and then use OpenROAD to map the RTL design to layout. A high-level compiler driver (e.g., GNU g++, Vitis v++) will be designed to orchestrate the different steps of the tool flow, allowing for the injection of user-defined constraints at various stages. The expected outcome is that users should be able to generate a physical design file ready for tape-out using only the HLS (C++) design and a physical constraints file.
