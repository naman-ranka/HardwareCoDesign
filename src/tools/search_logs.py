import os
import glob

def search_logs(query, workspace_dir=None):
    """
    Searches for a keyword in all OpenROAD logs and reports.
    Returns a string with matching lines and filenames.
    """
    if workspace_dir is None:
        # Default to relative path
        workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workspace'))
        
    search_dirs = [
        os.path.join(workspace_dir, "orfs_reports"),
        os.path.join(workspace_dir, "orfs_logs"),
        os.path.join(workspace_dir, "orfs_results")
    ]
    
    results = []
    
    # Robustly find all text files
    files = []
    for d in search_dirs:
        if os.path.exists(d):
            # We look for common log extensions
            for ext in ["*.log", "*.rpt", "*.txt", "*.v", "*.json"]:
                files.extend(glob.glob(os.path.join(d, "**", ext), recursive=True))
                
    if not files:
        return "No log files found to search."
        
    query_lower = query.lower()
    
    for fpath in files:
        try:
            with open(fpath, "r", errors='ignore') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if query_lower in line.lower():
                        # Found a match!
                        rel_path = os.path.relpath(fpath, workspace_dir)
                        results.append(f"File: {rel_path} | Line {i+1}: {line.strip()}")
                        
                        # Optimization: If we found 5 matches in one file, maybe stop? 
                        # For now, let's capture all.
        except Exception:
            continue
            
    if not results:
        return f"No matches found for '{query}'."
        
    return "\n".join(results[:50]) # Limit to 50 matches to avoid context overflow
