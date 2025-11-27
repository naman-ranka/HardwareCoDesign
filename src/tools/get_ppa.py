import os
import re
import glob

def get_ppa_metrics(log_dir):
    """
    Parses OpenROAD/Yosys logs to extract PPA metrics.
    
    Args:
        log_dir (str): Path to the directory containing logs (e.g., workspace/orfs_logs).
        
    Returns:
        dict: {
            "area_um2": float,
            "cell_count": int,
            "wns_ns": float, # Worst Negative Slack
            "tns_ns": float, # Total Negative Slack
            "power_uw": float,
            "errors": list
        }
    """
    metrics = {
        "area_um2": None,
        "cell_count": None,
        "wns_ns": None,
        "tns_ns": None,
        "power_uw": None,
        "errors": []
    }
    
    if not os.path.exists(log_dir):
        metrics["errors"].append(f"Log directory not found: {log_dir}")
        return metrics

    # 1. Parse Synthesis Reports (e.g., 1_1_yosys.stat.rpt)
    # Prioritize reports over logs
    # Robustly find sibling 'orfs_reports' dir
    workspace_dir = os.path.dirname(log_dir.rstrip(os.sep))
    reports_dir = os.path.join(workspace_dir, "orfs_reports")
    
    report_patterns = [
        os.path.join(log_dir, "**", "*yosys.stat.rpt"),
        os.path.join(reports_dir, "**", "*yosys.stat.rpt"),
        os.path.join(reports_dir, "**", "*synth_stat.txt")
    ]
    log_patterns = [
        os.path.join(log_dir, "**", "*yosys.log")
    ]
    
    found_reports = []
    for pattern in report_patterns:
        found_reports.extend(glob.glob(pattern, recursive=True))
        
    found_logs = []
    for pattern in log_patterns:
        found_logs.extend(glob.glob(pattern, recursive=True))
        
    # Pick the best file: latest report, else latest log
    latest_file = None
    if found_reports:
        latest_file = max(found_reports, key=os.path.getmtime)
    elif found_logs:
        latest_file = max(found_logs, key=os.path.getmtime)
        
    if latest_file:
        try:
            with open(latest_file, "r") as f:
                content = f.read()
                print(f"DEBUG: Content snippet:\n{content[:2000]}", flush=True)
                
                # Extract Chip Area
                # Pattern: "Chip area for module '\w+': \s+([0-9.]+)"
                # Robust: match "Chip area" ... ":" ... number
                area_match = re.search(r"Chip area for module.*:\s*([0-9.]+)", content)
                if area_match:
                    metrics["area_um2"] = float(area_match.group(1))
                    
                # Extract Cell Count
                # Pattern 1: "Number of cells: \s+([0-9]+)"
                cell_match = re.search(r"Number of cells:.*([0-9]+)", content)
                if cell_match:
                    metrics["cell_count"] = int(cell_match.group(1))
                else:
                    # Pattern 2: "   10  142.637      cells"
                    cell_match = re.search(r"^\s*([0-9]+)\s+.*cells", content, re.MULTILINE)
                    if cell_match:
                        metrics["cell_count"] = int(cell_match.group(1))
                    
        except Exception as e:
            metrics["errors"].append(f"Error parsing file {latest_file}: {e}")
    else:
        metrics["errors"].append("No Yosys log or report found.")

    # 2. Parse Timing Log (e.g., 3_..._sta.log or similar)
    # Since our flow failed early, we might not have STA logs.
    # But if we did, we'd look for "wns" or "slack".
    # For now, we focus on Synthesis metrics.
    
    return metrics
