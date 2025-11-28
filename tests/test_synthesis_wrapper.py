import os
import sys

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.wrappers import synthesis_tool

def main():
    print("Testing Synthesis Tool Wrapper (Rich Output)...")
    
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../workspace'))
    design_file = "synth_counter.v"
    
    # Ensure the file exists (created by previous tests)
    if not os.path.exists(os.path.join(workspace_dir, design_file)):
        print(f"Creating dummy {design_file}...")
        with open(os.path.join(workspace_dir, design_file), "w") as f:
            f.write("module synth_counter(input clk, output reg [3:0] q); always @(posedge clk) q <= q + 1; endmodule")

    print(f"Calling synthesis_tool('{design_file}', 'synth_counter')...")
    
    # This will run the actual Docker synthesis
    # synthesis_tool is a LangChain StructuredTool, so we use .invoke
    output = synthesis_tool.invoke({"design_file": design_file, "top_module": "synth_counter"})
    
    print("\n--- Tool Output ---")
    print(output)
    print("-------------------")
    
    if "Quick PPA Scan" in output and "Chip area" in output:
        print("✅ Rich Output Verified!")
    else:
        print("❌ Rich Output Missing or Synthesis Failed")

if __name__ == "__main__":
    main()
