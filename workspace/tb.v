// Testbench for up_counter_4bit
module tb;

    // Signals to connect to the DUT
    reg  clk;
    reg  rst;
    wire [3:0] count;

    // Instantiate the Device Under Test (DUT)
    up_counter_4bit dut (
        .clk(clk),
        .rst(rst),
        .count(count)
    );

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk; // 10ns period clock
    end

    // Test sequence
    initial begin
        integer error_count = 0;
        integer i;

        $display("Starting test for up_counter_4bit...");

        // 1. Test asynchronous reset
        $display("Step 1: Testing asynchronous reset...");
        rst = 1; // Assert reset
        #12;     // Wait for a duration longer than a clock cycle
        #1;      // Wait for propagation delay
        if (count !== 4'b0000) begin
            $display("ERROR: Reset failed. Expected count=0, got %d", count);
            error_count = error_count + 1;
        end
        rst = 0; // De-assert reset
        
        // Wait for the first rising edge after reset is de-asserted
        @(posedge clk);
        #1;
        if (count !== 4'b0001) begin
            $display("ERROR: Count did not increment to 1 after reset. Got %d", count);
            error_count = error_count + 1;
        end

        // 2. Test counting sequence from 2 to 15
        $display("Step 2: Testing counting sequence...");
        for (i = 2; i <= 15; i = i + 1) begin
            @(posedge clk);
            #1; // Wait for output to settle
            if (count !== i) begin
                $display("ERROR: Count mismatch. Expected %d, got %d", i, count);
                error_count = error_count + 1;
            end
        end

        // 3. Test rollover from 15 to 0
        $display("Step 3: Testing rollover...");
        @(posedge clk);
        #1;
        if (count !== 4'b0000) begin
            $display("ERROR: Rollover failed. Expected count=0, got %d", count);
            error_count = error_count + 1;
        end

        // 4. Test mid-cycle asynchronous reset
        $display("Step 4: Testing mid-cycle asynchronous reset...");
        // Let the counter run for a few cycles
        @(posedge clk); // count becomes 1
        @(posedge clk); // count becomes 2
        #2; // Wait for some time, not aligned with clock edge
        rst = 1; // Assert reset
        #1; // Wait for propagation
        if (count !== 4'b0000) begin
            $display("ERROR: Mid-cycle reset failed. Expected count=0, got %d", count);
            error_count = error_count + 1;
        end
        #10;
        rst = 0; // De-assert reset

        // Final check after mid-cycle reset
        @(posedge clk);
        #1;
        if (count !== 4'b0001) begin
            $display("ERROR: Count did not start from 1 after mid-cycle reset. Got %d", count);
            error_count = error_count + 1;
        end

        // Final test result
        if (error_count == 0) begin
            $display("TEST PASSED");
        end else begin
            $display("TEST FAILED with %d errors.", error_count);
        end

        $finish;
    end

endmodule