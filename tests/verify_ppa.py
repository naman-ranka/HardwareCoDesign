import os
import sys

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.get_ppa import get_ppa_metrics

def main():
    print("Verifying PPA Metrics Tool...")
    
    workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../workspace'))
    logs_dir = os.path.join(workspace_dir, "orfs_logs")
    
    if not os.path.exists(logs_dir):
        print("❌ Logs directory not found. Please run synthesis verification first.")
        sys.exit(1)
        
    print(f"Parsing logs in: {logs_dir}")
    
    metrics = get_ppa_metrics(logs_dir)
    
    print("\n--- Extracted Metrics ---")
    print(metrics)
    print("-------------------------")
    
    if metrics["cell_count"] is not None:
        print(f"PASS Cell Count: {metrics['cell_count']}")
        print(f"PASS Area: {metrics['area_um2']} um^2")
        print("\nPPA Metrics Verification PASSED!")
    else:
        print("FAIL Failed to extract Cell Count.")
        print(f"Errors: {metrics['errors']}")
        sys.exit(1)

if __name__ == "__main__":
    main()
