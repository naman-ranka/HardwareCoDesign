# SiliconCrew Project Roadmap & Verification Plan

This document outlines the step-by-step implementation plan for SiliconCrew. 
**Crucial Rule:** Every tool or component must be verified immediately after implementation before moving to the next step.

## Phase 1: The Foundation (Infrastructure)
- [ ] **Project Skeleton**
    - [ ] Create directory structure (`src/agents`, `src/tools`, `workspace`, etc.)
    - [ ] Set up Python environment (venv/poetry)
    - [ ] *Verification:* Script to check paths exist and python is executable.
- [ ] **Tool: Local Execution (Icarus Verilog)**
    - [ ] Implement `run_iverilog` wrapper.
    - [ ] *Verification:* Run a "Hello World" Verilog file via the wrapper and assert output.
- [ ] **Tool: Docker Bridge (OpenROAD)**
    - [ ] Implement `run_docker_command` wrapper with volume mounting.
    - [ ] *Verification:* Run `openroad -version` inside Docker via the wrapper and check output.

## Phase 2: The Inner Loop (RTL Coding & Verification)
- [ ] **Tool: Linter**
    - [ ] Implement `run_linter` (Verilator/Icarus lint mode).
    - [ ] *Verification:* Feed a buggy Verilog file and confirm the wrapper catches the syntax error.
- [ ] **Tool: Simulation**
    - [ ] Implement `run_simulation` (Compile + Run + Log Parse).
    - [ ] *Verification:* Run a simple counter testbench and confirm "PASS" status extraction.
- [ ] **Agent: RTL Coder**
    - [ ] Implement basic prompt and state connection.
    - [ ] *Verification:* Manually invoke the agent to generate a module and check if the file is written.
- [ ] **Agent: Verifier**
    - [ ] Implement verification logic.
    - [ ] *Verification:* Manually invoke the agent to run a test on existing code.
- [ ] **Orchestration: The Cycle**
    - [ ] Connect Coder <-> Verifier in LangGraph.
    - [ ] *Verification:* "The Loop Test" - Give a broken design and see if the system self-corrects after 1-2 iterations.

## Phase 3: The Outer Loop (Physical Design)
- [ ] **Tool: Synthesis**
    - [ ] Implement `run_synthesis` (Yosys via Docker).
    - [ ] *Verification:* Synthesize a counter and check for netlist generation.
- [ ] **Tool: PPA Metrics**
    - [ ] Implement parser for OpenROAD logs (Area, Slack, Power).
    - [ ] *Verification:* Parse a sample log file and assert extracted values.
- [ ] **Agent: PPA Analyst**
    - [ ] Integrate Docker tools into the agent.
    - [ ] *Verification:* Run the agent to perform a full P&R flow on a verified design.

## Phase 4: Intelligence & Refinement
- [ ] **State Management**
    - [ ] Implement iteration tracking and history.
    - [ ] *Verification:* Check state persistence across multiple agent steps.
- [ ] **Routing Logic**
    - [ ] Implement conditional edges (Simulation Fail -> Coder, Timing Fail -> Analyst).
    - [ ] *Verification:* Unit test the routing logic with mock states.
- [ ] **Benchmark**
    - [ ] Run the full system on an 8-bit Counter from scratch.
    - [ ] *Verification:* End-to-end success (RTL -> GDSII).
