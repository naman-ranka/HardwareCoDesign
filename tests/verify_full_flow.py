import os
import sys
from dotenv import load_dotenv

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.graph import create_graph
from src.state.state import DesignState

def main():
    load_dotenv()
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found.")
        sys.exit(1)
        
    print("Verifying Full Flow (Coder -> Verifier -> Synthesis -> PPA Analyst)...")
    
    app = create_graph()
    
    # Use a simple design that we know synthesizes quickly
    initial_state: DesignState = {
        "design_spec": "A 4-bit up-counter with asynchronous active-high reset.",
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
        
        metrics = final_state.get("ppa_metrics", {})
        print(f"PPA Metrics: {metrics}")
        
        if final_state["functional_valid"] and metrics.get("cell_count") is not None:
            print("✅ Full Flow Succeeded!")
            print("\n🎉 Full Flow Verification PASSED!")
        else:
            print("❌ Full Flow Failed.")
            if not final_state["functional_valid"]:
                print("Reason: Verification Failed.")
            elif metrics.get("cell_count") is None:
                print("Reason: PPA Extraction Failed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Execution Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
