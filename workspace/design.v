
module mux2 (
    input wire i0,
    input wire i1,
    input wire sel,
    output wire out
);

assign out = sel ? i1 : i0;

endmodule
