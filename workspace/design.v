module up_counter_4bit (
    input  wire clk,
    input  wire rst,
    output reg  [3:0] count
);

    // Asynchronous active-high reset and synchronous counter logic
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            // On reset, set the count to 0
            count <= 4'b0000;
        end else begin
            // On the positive edge of the clock, increment the count
            count <= count + 1;
        end
    end

endmodule