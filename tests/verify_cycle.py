import os
import sys
from dotenv import load_dotenv

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.graph import create_graph
from src.state.state import DesignState

def main():
    load_dotenv()
    print("Verifying Orchestration Cycle (Coder <-> Verifier)...")
    
    app = create_graph()
    
    initial_state: DesignState = {
        "design_spec": "A simple 2-to-1 Multiplexer (MUX) with 1-bit inputs a, b, select line sel, and output y.",
        "verilog_code": "",
        "testbench_code": "",
        "iteration_count": 0,
        "max_iterations": 3,
        "error_logs": [],
        "syntax_valid": False,
        "functional_valid": False,
        "ppa_metrics": {},
        "current_agent": "start",
        "messages": []
    }
    
    print(f"Goal: {initial_state['design_spec']}")
    
    try:
        # Run the graph
        final_state = app.invoke(initial_state)
        
        print("\n--- Final Result ---")
        print(f"Iterations: {final_state['iteration_count']}")
        print(f"Functional Valid: {final_state['functional_valid']}")
        
        if final_state["functional_valid"]:
            print("✅ Cycle succeeded! Design verified.")
            print("\n--- Final Verilog ---")
            print(final_state["verilog_code"])
            print("\n🎉 Orchestration Verification PASSED!")
        else:
            print("❌ Cycle failed to produce a valid design within max iterations.")
            print(f"Last Errors: {final_state['error_logs']}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Execution Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
