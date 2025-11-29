# 🚀 Deployment Guide: SiliconCrew Architect

This document outlines the strategy for deploying the SiliconCrew RTL Agent to cloud platforms (Railway, Render, AWS, etc.).

## 🏗️ Architecture: The "Inverted" Toolchain

To avoid complex "Docker-in-Docker" (DinD) setups, we use an **Inverted Architecture** for deployment.
Instead of the Python app spawning Docker containers, we run the Python app **inside** the OpenROAD Docker container.

### Comparison

| Environment | Host OS | Tool Execution | Architecture |
| :--- | :--- | :--- | :--- |
| **Local (Dev)** | Windows/Mac | `subprocess` calls `docker run ...` | App controls Docker |
| **Cloud (Prod)** | Linux (Container) | Direct binary execution (`/usr/bin/openroad`) | App lives inside Tool Container |

## 🐳 The Dockerfile

Create a `Dockerfile` in the root directory:

```dockerfile
# 1. Base Image: Start with the heavy EDA tools pre-installed
# This image contains OpenROAD, Yosys, KLayout, etc.
FROM openroad/flow-scripts:latest

# 2. Install Lighter Tools & Dependencies
# We need Icarus Verilog for simulation and Python for our Agent
RUN sudo apt-get update && sudo apt-get install -y \
    iverilog \
    python3-pip \
    git \
    graphviz

# 3. Set up Python Environment
WORKDIR /app
COPY requirements.txt .
# Note: openroad image might use system python, ensure compatibility
RUN pip3 install -r requirements.txt

# 4. Copy Application Code
COPY . /app

# 5. Expose Streamlit Port
EXPOSE 8501

# 6. Run the Agent
# We use the array format for CMD
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 🔧 Code Adjustments Required

To support this dual-mode (Local vs. Cloud), we need to update `src/tools/run_synthesis.py`.

### Current Logic (Local Only)
```python
run_docker_command(command="make ...", ...)
```

### Required Logic (Hybrid)
We need to detect if we are already inside a Docker container.

```python
def run_synthesis(...):
    # ... setup config.mk ...
    
    IS_IN_DOCKER = os.path.exists("/.dockerenv") or os.environ.get("KUBERNETES_SERVICE_HOST")
    
    if IS_IN_DOCKER:
        # Cloud Mode: Run directly
        # The 'make' command is available in the path
        cmd = f"cd {flow_dir} && make DESIGN_CONFIG={config_path}"
        subprocess.run(cmd, shell=True, check=True)
    else:
        # Local Mode: Use Wrapper
        run_docker_command(...)
```

## 🚀 Deployment Steps (Railway Example)

1.  **Push to GitHub:** Ensure your repo is up to date.
2.  **New Project on Railway:** Select "Deploy from GitHub repo".
3.  **Variables:** Add your `GOOGLE_API_KEY` in the Railway dashboard.
4.  **Build:** Railway will automatically detect the `Dockerfile` and build the image.
    *   *Note: The OpenROAD image is large (~5GB). The first build will take time.*
5.  **Success:** Your RTL Agent is now live on the web!
