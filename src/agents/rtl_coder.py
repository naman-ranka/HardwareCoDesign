import os
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.state.state import DesignState
from src.tools.wrappers import write_file, read_file, edit_file_tool, linter_tool
from src.config import DEFAULT_MODEL

# Initialize LLM
if "GOOGLE_API_KEY" not in os.environ:
    from dotenv import load_dotenv
    load_dotenv()

llm = ChatGoogleGenerativeAI(model=DEFAULT_MODEL, google_api_key=os.environ.get("GOOGLE_API_KEY"))

# Bind tools to the model
tools = [write_file, read_file, edit_file_tool, linter_tool]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are an expert Verilog/SystemVerilog RTL Engineer. 
Your goal is to write syntactically correct and functionally accurate Verilog modules based on specifications.

You have access to tools to write and check your code:
- `write_file`: Use this to save your Verilog code to a file (e.g., 'design.v').
- `read_file`: Use this to read existing code if you need to fix errors.
- `edit_file_tool`: Use this to surgically replace text (e.g., fixing a specific line) instead of rewriting the whole file.
- `linter_tool`: Use this to check for syntax errors.

Rules:
1. Always write the code to a file using `write_file` (for new code) or `edit_file_tool` (for fixes).
2. Check the syntax using `linter_tool`.
3. If there are syntax errors, fix them.
4. Once you are confident, finish by saying "RTL Generation Complete".
"""

def rtl_coder_node(state: DesignState) -> DesignState:
    """
    Agent node that generates or fixes Verilog code using Tool Calls.
    """
    print("🤖 RTL Coder: Generating code...")
    
    # Construct history
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    
    if state.get("error_logs"):
         # Fix Mode
         messages.append(HumanMessage(content=f"Previous Code had errors: {state['error_logs'][-1]}. Please fix."))
    else:
         # Gen Mode
         messages.append(HumanMessage(content=f"Design Specification: {state['design_spec']}"))

    # Invoke LLM
    response = llm_with_tools.invoke(messages)
    messages.append(response)
    
    # Process Tool Calls (Simple Loop)
    max_turns = 10  # Increased for read/edit cycles
    turn = 0
    final_code = state.get("verilog_code", "")
    
    while response.tool_calls and turn < max_turns:
        turn += 1
        print(f"  Tool Call Loop {turn}: {len(response.tool_calls)} calls")

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]

            output = ""
            if tool_name == "write_file":
                output = write_file.invoke(tool_args)
                final_code = tool_args.get("content", "")

            elif tool_name == "read_file":
                output = read_file.invoke(tool_args)

            elif tool_name == "edit_file_tool":
                output = edit_file_tool.invoke(tool_args)
                # If we edit, we should ideally re-read the file to update final_code,
                # or trust the file system. For state consistency, let's try to read it back next turn if needed.
                # But to update `final_code` variable right now, we need to read the file.
                # Let's do a quick read if edit was successful.
                if "Success" in output:
                    filename = tool_args.get("filename")
                    try:
                        with open(os.path.abspath(os.path.join(os.environ.get("RTL_WORKSPACE", "workspace"), filename)), "r") as f:
                            final_code = f.read()
                    except:
                        pass

            elif tool_name == "linter_tool":
                output = linter_tool.invoke(tool_args)

            messages.append(ToolMessage(content=output, tool_call_id=tool_id))

        # Get next response
        response = llm_with_tools.invoke(messages)
        messages.append(response)
        
    return {
        "verilog_code": final_code,
        "messages": [AIMessage(content="**RTL Coder**: " + response.content)]
    }
