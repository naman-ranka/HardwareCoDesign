import os
import sys

# Add src to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.tools.search_logs import search_logs

def main():
    print("Testing Search Logs Tool...")
    
    # Test 1: Search for Area
    print("\n--- Searching for 'Chip area' ---")
    results = search_logs("Chip area")
    print(results)
    
    if "Chip area" in results:
        print("✅ Found Area info")
    else:
        print("❌ Failed to find Area info")

    # Test 2: Search for 'cells'
    print("\n--- Searching for 'cells' ---")
    results = search_logs("cells")
    print(results)
    
    if "cells" in results:
        print("✅ Found Cell info")
    else:
        print("❌ Failed to find Cell info")

if __name__ == "__main__":
    main()
