module Counter6(
    input  logic clk,
    input  inc,
    input  clear,
    output logic [3:0] out,
    output logic inc_next
);
always @(posedge clk) begin
    if (clear) begin
        out <= 0;
    end
    else if ( out == 4'd5 && inc ) begin
        out <= 0;
    end
    else if ( inc ) begin
        out <= out + 1'd1;
    end
    else begin
        out <= out;
    end
end

assign inc_next = (out == 4'd5) && inc;
endmodule