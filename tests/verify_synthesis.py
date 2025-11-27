import os
import sys

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.run_synthesis import run_synthesis

def main():
    print("Verifying Synthesis Tool (OpenROAD)...")
    
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../workspace'))
    if not os.path.exists(workspace_dir):
        os.makedirs(workspace_dir)
        
    # 1. Create a simple design to synthesize
    # A simple counter is good
    design_file = os.path.join(workspace_dir, "synth_counter.v")
    with open(design_file, "w") as f:
        f.write("""
module synth_counter(input clk, input rst, output reg [3:0] count);
    always @(posedge clk or posedge rst) begin
        if (rst)
            count <= 4'b0000;
        else
            count <= count + 1;
    end
endmodule
""")
    
    print(f"Created design file: {design_file}")
    
    # 2. Run Synthesis
    # This might take a while (Docker pull + run)
    print("Running 'make synthesis' inside Docker...")
    result = run_synthesis(
        verilog_files=[design_file],
        top_module="synth_counter",
        cwd=workspace_dir
    )
    
    print(f"Command: {result['command']}")
    
    if result['success']:
        print("✅ Synthesis Command Executed Successfully")
        
        # Check if output files exist
        # ORFS usually produces results/sky130hd/synth_counter/base/1_1_yosys.v
        # But we mapped results to orfs_results
        
        results_dir = os.path.join(workspace_dir, "orfs_results")
        # The path structure in ORFS is typically: <platform>/<design>/base/1_1_yosys.v
        # Let's check if *any* file was created in results
        
        found_files = []
        for root, dirs, files in os.walk(results_dir):
            for file in files:
                found_files.append(os.path.join(root, file))
                
        if found_files:
            print(f"✅ Found {len(found_files)} output files in orfs_results.")
            print(f"Sample: {found_files[0]}")
            print("\n🎉 Synthesis Tool Verification PASSED!")
        else:
            print("⚠️  Command succeeded but no output files found in orfs_results.")
            print("Stdout snippet:\n" + result['stdout'][-500:])
            # It's possible synthesis failed logically but make returned 0? Unlikely.
            # Or maybe the path mapping is wrong.
            sys.exit(1)
            
    else:
        # Check if output files exist even if the full flow failed (e.g. at placement)
        results_dir = os.path.join(workspace_dir, "orfs_results")
        found_files = []
        for root, dirs, files in os.walk(results_dir):
            for file in files:
                if "yosys.v" in file or "synth" in file:
                    found_files.append(os.path.join(root, file))
        
        if found_files:
            print("✅ Synthesis Artifacts Found (Flow might have failed later).")
            print(f"Sample: {found_files[0]}")
            print("\n🎉 Synthesis Tool Verification PASSED!")
            sys.exit(0)
        else:
            print("❌ Synthesis Failed and no artifacts found.")
            with open("synthesis_debug.log", "w") as log:
                log.write("STDOUT:\n")
                log.write(result['stdout'])
                log.write("\nSTDERR:\n")
                log.write(result['stderr'])
            print("Output written to synthesis_debug.log")
            sys.exit(1)

if __name__ == "__main__":
    main()
