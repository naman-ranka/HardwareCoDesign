
module tb_mux2;
    reg i0;
    reg i1;
    reg sel;
    wire out;

    mux2 dut (.i0(i0), .i1(i1), .sel(sel), .out(out));

    initial begin
        // Test Case 1: sel = 0, i0 = 0, i1 = 1 => out = i0 = 0
        i0 = 0; i1 = 1; sel = 0; #10;
        if (out !== 0) begin $display("TEST FAILED: Case 1"); $finish; end

        // Test Case 2: sel = 0, i0 = 1, i1 = 0 => out = i0 = 1
        i0 = 1; i1 = 0; sel = 0; #10;
        if (out !== 1) begin $display("TEST FAILED: Case 2"); $finish; end

        // Test Case 3: sel = 1, i0 = 0, i1 = 1 => out = i1 = 1
        i0 = 0; i1 = 1; sel = 1; #10;
        if (out !== 1) begin $display("TEST FAILED: Case 3"); $finish; end

        // Test Case 4: sel = 1, i0 = 1, i1 = 0 => out = i1 = 0
        i0 = 1; i1 = 0; sel = 1; #10;
        if (out !== 0) begin $display("TEST FAILED: Case 4"); $finish; end

        $display("TEST PASSED");
        $finish;
    end

endmodule
