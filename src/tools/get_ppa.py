import os
import re
import glob

def get_ppa_metrics(log_dir):
    """
    Robustly extracts PPA metrics by scanning multiple directories and file types.
    """
    metrics = {
        "area_um2": None,
        "cell_count": None,
        "wns_ns": None,
        "tns_ns": None,
        "power_uw": None,
        "errors": []
    }
    
    # Define search paths
    # We assume log_dir is .../workspace/orfs_logs
    workspace_dir = os.path.dirname(log_dir.rstrip(os.sep))
    search_dirs = [
        os.path.join(workspace_dir, "orfs_reports"),
        os.path.join(workspace_dir, "orfs_logs"),
        os.path.join(workspace_dir, "orfs_results"),
        log_dir
    ]
    
    # Helper to find files
    def find_files(pattern):
        files = []
        for d in search_dirs:
            if os.path.exists(d):
                files.extend(glob.glob(os.path.join(d, "**", pattern), recursive=True))
        return sorted(files, key=os.path.getmtime, reverse=True) # Newest first

    # 1. Extract Area & Cell Count (Synthesis Reports)
    area_files = find_files("*stat.rpt") + find_files("*yosys.log")
    print(f"DEBUG: Found area files: {area_files}")
    for fpath in area_files:
        try:
            with open(fpath, "r") as f:
                content = f.read()
                print(f"DEBUG: Reading {fpath}")
                print(f"DEBUG: Content snippet: {content[:200]}")
                
                if metrics["area_um2"] is None:
                    # Match: "Chip area for module '\synth_counter': 100.096000"
                    # Simplified Regex: Chip area.*: [number]
                    match = re.search(r"Chip area.*:\s*([0-9.]+)", content, re.IGNORECASE)
                    if match: 
                        metrics["area_um2"] = float(match.group(1))
                        print(f"DEBUG: Found Area: {metrics['area_um2']}")
                    
                if metrics["cell_count"] is None:
                    # Match: "Number of cells:       12"
                    # Simplified Regex: Number of cells.*: [number]
                    match = re.search(r"Number of cells.*:\s*([0-9]+)", content, re.IGNORECASE)
                    if match: 
                        metrics["cell_count"] = int(match.group(1))
                        print(f"DEBUG: Found Cell Count: {metrics['cell_count']}")
        except: pass
        if metrics["area_um2"] and metrics["cell_count"]: break

    # 2. Extract Timing (STA Logs/Reports)
    timing_files = find_files("*sta.log") + find_files("*timing.rpt")
    for fpath in timing_files:
        try:
            with open(fpath, "r") as f:
                content = f.read()
                # Look for WNS (Worst Negative Slack)
                # Pattern: "wns ... -1.23" or "slack (VIOLATED) : -1.23"
                if metrics["wns_ns"] is None:
                    match = re.search(r"wns\s+([0-9.-]+)", content, re.IGNORECASE)
                    if match: metrics["wns_ns"] = float(match.group(1))
                    
                    # Fallback: OpenROAD report style
                    match = re.search(r"slack.*:\s*([0-9.-]+)", content, re.IGNORECASE)
                    if match: metrics["wns_ns"] = float(match.group(1))
        except: pass
        if metrics["wns_ns"]: break

    # 3. Extract Power (Power Reports)
    power_files = find_files("*power.rpt") + find_files("*sta.log")
    for fpath in power_files:
        try:
            with open(fpath, "r") as f:
                content = f.read()
                # Pattern: "Total Power ... 1.23e-05"
                if metrics["power_uw"] is None:
                    match = re.search(r"Total Power\s+([0-9.eE+-]+)", content, re.IGNORECASE)
                    if match: metrics["power_uw"] = float(match.group(1))
        except: pass
        if metrics["power_uw"]: break

    return metrics
