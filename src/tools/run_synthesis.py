import os
import sys
from .run_docker import run_docker_command

def run_synthesis(verilog_files, top_module, platform="sky130hd", cwd=None):
    """
    Runs Yosys synthesis using the OpenROAD Flow Scripts (ORFS) via Docker.
    
    Args:
        verilog_files (list): List of absolute paths to .v files.
        top_module (str): Name of the top-level module.
        platform (str): Target platform (default: sky130hd).
        cwd (str): Workspace directory (optional).
        
    Returns:
        dict: {
            "success": bool,
            "stdout": str,
            "stderr": str,
            "metrics": dict (placeholder for now)
        }
    """
    if cwd is None:
        # Default to workspace dir relative to this file
        cwd = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../workspace'))
        
    if not os.path.exists(cwd):
        os.makedirs(cwd)

    # 1. Prepare Directories for ORFS outputs
    # We want to persist results, logs, and reports
    results_dir = os.path.join(cwd, "orfs_results")
    logs_dir = os.path.join(cwd, "orfs_logs")
    reports_dir = os.path.join(cwd, "orfs_reports")
    
    for d in [results_dir, logs_dir, reports_dir]:
        if not os.path.exists(d):
            os.makedirs(d)
            
    # 2. Generate config.mk
    # We need to map the local file paths to /workspace paths for the config
    # Assuming verilog_files are inside the workspace or accessible via /workspace mount
    
    # Convert local paths to container paths
    # If file is C:/Users/.../workspace/design.v, container path is /workspace/design.v
    container_verilog_files = []
    for f in verilog_files:
        # Simple heuristic: replace local workspace path with /workspace
        # This assumes files are IN the workspace.
        if cwd in os.path.abspath(f):
            rel_path = os.path.relpath(f, cwd).replace("\\", "/")
            container_verilog_files.append(f"/workspace/{rel_path}")
        else:
            # If file is outside workspace, we might have an issue unless we mount it.
            # For now, assume strict workspace usage.
            print(f"Warning: File {f} is not in workspace {cwd}. It may not be visible to Docker.")
            container_verilog_files.append(f"/workspace/{os.path.basename(f)}")

    # Generate dummy SDC file if not provided (ORFS often requires it)
    sdc_file = os.path.join(cwd, "constraints.sdc")
    if not os.path.exists(sdc_file):
        with open(sdc_file, "w") as f:
            f.write(f"create_clock -period 10 [get_ports clk]")
            
    config_content = f"""
export DESIGN_NAME = {top_module}
export PLATFORM = {platform}
export VERILOG_FILES = {" ".join(container_verilog_files)}
export SDC_FILE = /workspace/constraints.sdc
export CORE_UTILIZATION = 5
export CORE_ASPECT_RATIO = 1
export CORE_MARGIN = 2
"""
    
    config_file = os.path.join(cwd, "config.mk")
    with open(config_file, "w") as f:
        f.write(config_content)
        
    # 3. Construct Docker Command
    # We mount the local output dirs to the ORFS flow directories
    volumes = [
        f"{results_dir}:/OpenROAD-flow-scripts/flow/results",
        f"{logs_dir}:/OpenROAD-flow-scripts/flow/logs",
        f"{reports_dir}:/OpenROAD-flow-scripts/flow/reports"
    ]
    
    # Command: make DESIGN_CONFIG=/workspace/config.mk
    make_cmd = "make DESIGN_CONFIG=/workspace/config.mk"
    
    print(f"🚀 Starting Synthesis for {top_module}...")
    result = run_docker_command(
        command=make_cmd,
        workspace_path=cwd,
        volumes=volumes
    )
    
    return result
