import streamlit as st
import os
import sqlite3
import shutil
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver

# Architect (Single Agent)
from src.agents.architect import create_architect_agent, SYSTEM_PROMPT as ARCHITECT_PROMPT

# Multi-Agent
from src.graph.graph import create_graph as create_multi_agent_graph

from src.utils.session_manager import SessionManager
from src.utils.visualizers import render_waveform, render_gds

# Load environment
load_dotenv()

st.set_page_config(page_title="SiliconCrew Architect", layout="wide", initial_sidebar_state="expanded")

# Initialize Manager
session_manager = SessionManager(base_dir=os.path.join(os.path.dirname(__file__), 'workspace'), 
                               db_path=os.path.join(os.path.dirname(__file__), 'state.db'))

# --- Session Logic ---
if "current_session" not in st.session_state:
    st.session_state.current_session = None

# Set Workspace Env Var (if session active)
if st.session_state.current_session:
    CURRENT_WORKSPACE = session_manager.get_workspace_path(st.session_state.current_session)
    os.environ["RTL_WORKSPACE"] = CURRENT_WORKSPACE
else:
    CURRENT_WORKSPACE = None

DB_PATH = session_manager.db_path

# Custom CSS
st.markdown("""
<style>
    .stChatMessage { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }
    .tool-call { background-color: transparent; padding: 0.5rem; border-radius: 0.3rem; border-left: 3px solid #2196f3; font-family: monospace; margin-bottom: 0.5rem; }
    .tool-output { background-color: #f0f2f6; padding: 0.5rem; border-radius: 0.3rem; font-family: monospace; font-size: 0.9em; border-left: 3px solid #ff4b4b; }

    /* Status indicators */
    .status-pass { color: green; font-weight: bold; }
    .status-fail { color: red; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Helper to parse message content
def get_clean_content(msg):
    content = msg.content
    if isinstance(content, list):
        text_blocks = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    text_blocks.append(block.get("text", ""))
            elif isinstance(block, str):
                text_blocks.append(block)
        return "\n".join(text_blocks)
    return str(content)

# --- UI Functions ---

def render_home():
    st.title("SiliconCrew 🤖")
    st.markdown("### Autonomous RTL Design Agent")
    st.divider()

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("🚀 Start New Session")
        with st.form("new_session_home"):
            tag = st.text_input("Session Name (Required)", placeholder="e.g., LFSR_Design")

            # Mode Selection
            mode = st.radio("Select Design Mode",
                           ["Single Agent (Architect)", "Multi-Agent Crew (Pipeline)"],
                           help="Single Agent: Interactive chat with one powerful agent.\nMulti-Agent: Autonomous pipeline with specialized agents.")

            if st.form_submit_button("Create & Start", type="primary", use_container_width=True):
                if tag:
                    try:
                        new_session = session_manager.create_session(tag=tag)
                        st.session_state.current_session = new_session
                        st.session_state.agent_mode = "multi" if "Multi" in mode else "single"
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                    except FileExistsError as e:
                        st.error(str(e))
                else:
                    st.error("Please enter a session name.")

    with col2:
        st.subheader("📂 Load Previous Session")
        sessions = session_manager.get_all_sessions()
        if sessions:
            for sess in sessions:
                c1, c2 = st.columns([0.8, 0.2])
                if c1.button(f"📄 {sess}", key=f"load_{sess}", use_container_width=True):
                    st.session_state.current_session = sess
                    # Default to single if not tracked (could save mode in metadata later)
                    st.session_state.agent_mode = "single"
                    st.rerun()
                if c2.button("🗑️", key=f"del_{sess}"):
                    pass
        else:
            st.info("No previous sessions found.")
            
    st.divider()
    if st.button("🗑️ Clear All History", type="secondary"):
        session_manager.clear_all_sessions()
        st.rerun()

def render_workspace():
    # --- Main Layout ---
    # Top Bar
    top_col1, top_col2, top_col3 = st.columns([0.1, 0.7, 0.2])
    with top_col1:
        if st.button("🏠", help="Back to Home"):
            st.session_state.current_session = None
            st.rerun()
    with top_col2:
        mode_label = "Multi-Agent 👥" if st.session_state.get("agent_mode") == "multi" else "Single Architect 👤"
        st.caption(f"Session: `{st.session_state.current_session}` | Mode: **{mode_label}**")

    col1, col2 = st.columns([1.2, 0.8])

    # Column 2: Live Workspace (Code & Metrics) - SAME for both modes
    with col2:
        # Header with "Close File" if viewing a specific file
        if st.session_state.get("selected_file"):
            c_head_1, c_head_2 = st.columns([0.8, 0.2])
            c_head_1.subheader(f"📄 {os.path.basename(st.session_state.selected_file)}")
            if c_head_2.button("❌ Close", use_container_width=True):
                st.session_state.selected_file = None
                st.rerun()
                
            file_path = os.path.join(CURRENT_WORKSPACE, st.session_state.selected_file)
            if os.path.exists(file_path):
                try:
                    with open(file_path, "r", errors='ignore') as f:
                        content = f.read()
                    st.code(content, language="verilog" if file_path.endswith(".v") else "text")
                except Exception as e:
                    st.error(f"Error reading file: {e}")
            else:
                st.error("File not found.")
                
        else:
            st.subheader("Live Workspace")
            tab_code, tab_wave, tab_layout = st.tabs(["📝 Code", "📈 Waveform", "🗺️ Layout"])
            
            with tab_code:
                file_viewer_placeholder = st.empty()
                def render_files():
                    with file_viewer_placeholder.container():
                        if os.path.exists(CURRENT_WORKSPACE):
                            all_files = sorted(os.listdir(CURRENT_WORKSPACE))
                            files = [f for f in all_files if f.endswith(('.v', '.sv', '.rpt', '.txt', '.log')) and os.path.isfile(os.path.join(CURRENT_WORKSPACE, f))]
                        else:
                            files = []

                        if files:
                            sub_tabs = st.tabs(files)
                            for i, file_name in enumerate(files):
                                with sub_tabs[i]:
                                    file_path = os.path.join(CURRENT_WORKSPACE, file_name)
                                    try:
                                        with open(file_path, "r", errors='ignore') as f:
                                            content = f.read()
                                        st.code(content, language="verilog" if file_name.endswith(".v") else "text")
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                        else:
                            st.info("Waiting for generated files...")
                render_files()

            with tab_wave:
                if os.path.exists(CURRENT_WORKSPACE):
                    vcd_files = [f for f in os.listdir(CURRENT_WORKSPACE) if f.endswith(".vcd")]
                    if vcd_files:
                        selected_vcd = st.selectbox("Select VCD", vcd_files)
                        if selected_vcd:
                            render_waveform(os.path.join(CURRENT_WORKSPACE, selected_vcd))
                    else:
                        st.info("No VCD files found. Run simulation to generate waveforms.")
                else:
                    st.info("Workspace not ready.")

            with tab_layout:
                gds_files = []
                if os.path.exists(CURRENT_WORKSPACE):
                    for root, dirs, files in os.walk(CURRENT_WORKSPACE):
                        for file in files:
                            if file.endswith(".gds"):
                                rel_path = os.path.relpath(os.path.join(root, file), CURRENT_WORKSPACE)
                                gds_files.append(rel_path)
                
                if gds_files:
                    selected_gds = st.selectbox("Select Layout (GDS)", gds_files)
                    if selected_gds:
                        render_gds(os.path.join(CURRENT_WORKSPACE, selected_gds))
                else:
                    st.info("No GDS files found. Run synthesis to generate layout.")

    # Column 1: Chat Interface
    with col1:
        st.subheader("Chat")
        
        # Initialize Agent based on Mode
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        memory = SqliteSaver(conn)
        
        mode = st.session_state.get("agent_mode", "single")

        if mode == "single":
            agent_graph = create_architect_agent(checkpointer=memory)
        else:
            # Multi-Agent doesn't necessarily need the same checkpointer structure if it's StateGraph(DesignState)
            # But we can try passing it if the graph compiles with it.
            # Our DesignState uses `messages` list, so history should be preserved.
            # However, create_graph() in src/graph/graph.py doesn't take checkpointer arg yet.
            # We'll just instantiate it.
            agent_graph = create_multi_agent_graph()

        config = {"configurable": {"thread_id": st.session_state.current_session}}
        
        # Recover State
        # For Single Agent, state["messages"] is the history.
        # For Multi Agent, state["messages"] is ALSO the history (we added it to TypedDict).
        try:
            current_state = agent_graph.get_state(config)
        except Exception:
            current_state = None

        # Render History
        if current_state and current_state.values and "messages" in current_state.values:
            for msg in current_state.values["messages"]:
                if isinstance(msg, SystemMessage): continue
                
                role = "user"
                if isinstance(msg, AIMessage):
                    role = "assistant"
                    with st.chat_message(role):
                        # Tool Calls (Single Agent only usually)
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                args_str = str(tool_call['args'])
                                short_args = (args_str[:100] + '...') if len(args_str) > 100 else args_str
                                st.markdown(f"<div class='tool-call'>🛠️ Calling <b>{tool_call['name']}</b></div>", unsafe_allow_html=True)
                                with st.expander(f"Arguments: {short_args}", expanded=False):
                                    st.code(args_str)
                        
                        clean_text = get_clean_content(msg)
                        if clean_text:
                            st.markdown(clean_text)
                elif hasattr(msg, "tool_call_id"): # ToolMessage
                    role = "tool"
                    with st.chat_message(role):
                        with st.expander("🛠️ Tool Output", expanded=False):
                            st.markdown(f"```\n{msg.content}\n```")
                else:
                     # User Message
                     with st.chat_message("user"):
                         st.markdown(msg.content)
        else:
            if mode == "single":
                st.info("👋 Hi! I'm the Architect. What hardware shall we build today?")
            else:
                st.info("👥 SiliconCrew Team Ready. Describe the design specification.")

        # Input
        if prompt := st.chat_input("Ex: Design an 8-bit counter"):
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant"):
                status_container = st.status("Working...", expanded=True)
                response_placeholder = st.empty()
                full_response = ""
                
                try:
                    if mode == "single":
                        # SINGLE AGENT LOGIC
                        input_messages = []
                        snapshot = agent_graph.get_state(config)
                        if not snapshot.values or not snapshot.values.get("messages"):
                            input_messages.append(SystemMessage(content=ARCHITECT_PROMPT))

                        input_messages.append(("user", prompt))
                        config["recursion_limit"] = 50

                        events = agent_graph.stream({"messages": input_messages}, config)

                        for event in events:
                            if "agent" in event:
                                msg = event["agent"]["messages"][-1]
                                if hasattr(msg, "tool_calls") and msg.tool_calls:
                                    for tool_call in msg.tool_calls:
                                        status_container.markdown(f"**🛠️ Calling {tool_call['name']}**")
                                
                                clean_text = get_clean_content(msg)
                                if clean_text:
                                    full_response = clean_text
                                    response_placeholder.markdown(full_response)

                            elif "tools" in event:
                                msg = event["tools"]["messages"][-1]
                                content = msg.content
                                status_container.markdown(f"**📄 Output:**\n```\n{content[:500]}...\n```")
                                if "Successfully wrote to" in content:
                                    render_files()
                                    status_container.success(f"Updated file.")
                                elif "FAILED" in content:
                                    status_container.error("Tool Failed. Retrying...")
                                elif "PASSED" in content:
                                    status_container.success("Verification Passed!")

                        status_container.update(label="Finished!", state="complete", expanded=False)

                    else:
                        # MULTI AGENT LOGIC
                        # Initial State
                        initial_state = {
                            "design_spec": prompt,
                            "iteration_count": 0,
                            "max_iterations": 3,
                            "messages": [HumanMessage(content=prompt)],
                            "error_logs": [],
                            "verilog_code": "",
                            "testbench_code": "",
                            "functional_valid": False
                        }

                        # Use update_state if session exists to preserve history?
                        # Ideally we load existing state, but for this demo, let's treat new prompt as new spec logic
                        # Or better: merge.

                        events = agent_graph.stream(initial_state, config)

                        for event in events:
                            # Event is a dict like {'rtl_coder': {'verilog_code': ..., 'messages': ...}}
                            for node_name, state_update in event.items():
                                status_container.markdown(f"**🔄 Node: {node_name}**")
                                
                                if "messages" in state_update and state_update["messages"]:
                                    latest_msg = state_update["messages"][-1]
                                    content = get_clean_content(latest_msg)
                                    response_placeholder.markdown(content)

                                    # If generated code, update tabs
                                    if "verilog_code" in state_update or "testbench_code" in state_update:
                                        render_files()

                                if node_name == "verifier":
                                    if state_update.get("functional_valid"):
                                        status_container.success("Verification PASSED ✅")
                                    else:
                                        status_container.error("Verification FAILED ❌")

                        status_container.update(label="Workflow Complete!", state="complete", expanded=False)

                except Exception as e:
                    status_container.update(label="Error", state="error")
                    st.error(f"❌ Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    
        conn.close()

# --- Main Routing ---
if "current_session" not in st.session_state or st.session_state.current_session is None:
    render_home()
else:
    CURRENT_WORKSPACE = session_manager.get_workspace_path(st.session_state.current_session)
    os.environ["RTL_WORKSPACE"] = CURRENT_WORKSPACE
    render_workspace()
