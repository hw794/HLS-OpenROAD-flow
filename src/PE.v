module PE (
    input logic clk,
    input logic reset,

    input logic [15:0] data_in_a, 
    input logic [15:0] data_in_b, 
    input logic [31:0] acc_in,    
    input logic val_in,           
    input logic rdy_in,           

    output logic [15:0] data_out_a, 
    output logic [15:0] data_out_b, 
    output logic [31:0] acc_out,    
    output logic val_out,          
    output logic rdy_out            
);

    always_ff @(posedge clk) begin
        if (reset) begin
            acc_out <= 0;
            val_out <= 0;
        end else if (val_in && rdy_in) begin
            acc_out <= acc_in + (data_in_a * data_in_b);
            val_out <= 1;
        end else begin
            val_out <= 0;
        end
    end

    assign data_out_a = data_in_a;
    assign data_out_b = data_in_b;

    assign rdy_out = rdy_in;

endmodule