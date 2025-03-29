// Auto-generated top module
module SystolicArray(
  input logic clk,
  input logic reset,
  input logic [15:0] A_0_0,
  input logic [15:0] A_0_1,
  input logic [15:0] A_1_0,
  input logic [15:0] A_1_1,
  input logic [15:0] B_0_0,
  input logic [15:0] B_0_1,
  input logic [15:0] B_1_0,
  input logic [15:0] B_1_1,
  output logic [31:0] C_0_0,
  output logic [31:0] C_0_1,
  output logic [31:0] C_1_0,
  output logic [31:0] C_1_1
);

// Internal nets
  wire [15:0] data_PE_0_0_to_PE_0_1;
  wire [15:0] data_PE_0_0_to_PE_1_0;
  wire val_PE_0_0_to_PE_0_1;
  wire rdy_PE_0_0_to_PE_0_1;
  wire [15:0] data_PE_0_1_to_PE_0_2;
  wire [15:0] data_PE_0_1_to_PE_1_1;
  wire val_PE_0_1_to_PE_1_1;
  wire rdy_PE_0_1_to_PE_1_1;
  wire [15:0] data_PE_1_0_to_PE_1_1;
  wire [15:0] data_PE_1_0_to_PE_2_0;
  wire val_PE_1_0_to_PE_1_1;
  wire rdy_PE_1_0_to_PE_1_1;
  wire [15:0] data_PE_1_1_to_PE_1_2;
  wire [15:0] data_PE_1_1_to_PE_2_1;
  wire val_PE_1_1_to_PE_1_2;
  wire rdy_PE_1_1_to_PE_1_2;

  // Instance of PE
  PE PE_0_0 (
    .clk(clk),
    .reset(reset),
    .data_in_a(A_0_0),
    .data_in_b(B_0_0),
    .acc_in(0),
    .val_in(1),
    .rdy_in(1),
    .data_out_a(data_PE_0_0_to_PE_0_1),
    .data_out_b(data_PE_0_0_to_PE_1_0),
    .acc_out(C_0_0),
    .val_out(val_PE_0_0_to_PE_0_1),
    .rdy_out(rdy_PE_0_0_to_PE_0_1)
  );

  // Instance of PE
  PE PE_0_1 (
    .clk(clk),
    .reset(reset),
    .data_in_a(data_PE_0_0_to_PE_0_1),
    .data_in_b(B_0_1),
    .acc_in(C_0_0),
    .val_in(val_PE_0_0_to_PE_0_1),
    .rdy_in(rdy_PE_0_0_to_PE_0_1),
    .data_out_a(data_PE_0_1_to_PE_0_2),
    .data_out_b(data_PE_0_1_to_PE_1_1),
    .acc_out(C_0_1),
    .val_out(val_PE_0_1_to_PE_1_1),
    .rdy_out(rdy_PE_0_1_to_PE_1_1)
  );

  // Instance of PE
  PE PE_1_0 (
    .clk(clk),
    .reset(reset),
    .data_in_a(A_1_0),
    .data_in_b(data_PE_0_0_to_PE_1_0),
    .acc_in(C_0_0),
    .val_in(val_PE_0_0_to_PE_1_0),
    .rdy_in(rdy_PE_0_0_to_PE_1_0),
    .data_out_a(data_PE_1_0_to_PE_1_1),
    .data_out_b(data_PE_1_0_to_PE_2_0),
    .acc_out(C_1_0),
    .val_out(val_PE_1_0_to_PE_1_1),
    .rdy_out(rdy_PE_1_0_to_PE_1_1)
  );

  // Instance of PE
  PE PE_1_1 (
    .clk(clk),
    .reset(reset),
    .data_in_a(data_PE_1_0_to_PE_1_1),
    .data_in_b(data_PE_0_1_to_PE_1_1),
    .acc_in(C_0_1),
    .val_in(val_PE_0_1_to_PE_1_1),
    .rdy_in(rdy_PE_0_1_to_PE_1_1),
    .data_out_a(data_PE_1_1_to_PE_1_2),
    .data_out_b(data_PE_1_1_to_PE_2_1),
    .acc_out(C_1_1),
    .val_out(val_PE_1_1_to_PE_1_2),
    .rdy_out(rdy_PE_1_1_to_PE_1_2)
  );

endmodule
