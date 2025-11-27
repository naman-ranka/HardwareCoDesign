import os
import sys
from dotenv import load_dotenv

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.ppa_analyst import ppa_analyst_node
from src.state.state import DesignState

def main():
    load_dotenv()
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found in environment variables.")
        sys.exit(1)
    else:
        print("✅ GOOGLE_API_KEY loaded.")
    
    # Ensure we have logs from the previous step (Synthesis)
    # The verify_synthesis.py should have run before this.
    
    initial_state: DesignState = {
        "design_spec": "A 4-bit up-counter with asynchronous active-high reset.",
        "verilog_code": "", # Not needed for this test, as we read logs
        "testbench_code": "",
        "iteration_count": 0,
        "max_iterations": 5,
        "error_logs": [],
        "syntax_valid": True,
        "functional_valid": True,
        "ppa_metrics": {},
        "current_agent": "ppa_analyst",
        "messages": []
    }
    
    try:
        new_state = ppa_analyst_node(initial_state)
        
        metrics = new_state["ppa_metrics"]
        print("\n--- Extracted Metrics ---")
        print(metrics)
        
        print("\n--- Agent Analysis ---")
        # The last message should be the analysis
        print(new_state["messages"][-1])
        print("----------------------")
        
        if metrics.get("cell_count") is not None:
            print("✅ Metrics Extraction Successful.")
        else:
            print("⚠️  Metrics Extraction Failed (expected if logs are missing/bad).")
            
        if "PPA Analysis:" in new_state["messages"][-1]:
            print("✅ Agent Analysis Received.")
            print("\n🎉 PPA Analyst Verification PASSED!")
        else:
            print("❌ Agent Analysis Missing or Malformed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Agent Execution Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
