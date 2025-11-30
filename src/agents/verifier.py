import os
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.state.state import DesignState
from src.tools.wrappers import write_file, simulation_tool, waveform_tool
from src.config import DEFAULT_MODEL

# Initialize LLM
if "GOOGLE_API_KEY" not in os.environ:
    from dotenv import load_dotenv
    load_dotenv()

llm = ChatGoogleGenerativeAI(model=DEFAULT_MODEL, google_api_key=os.environ.get("GOOGLE_API_KEY"))

# Bind tools
tools = [write_file, simulation_tool, waveform_tool]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are an expert Verification Engineer.
Your goal is to verify the RTL design using a testbench.

Tools:
- `write_file`: Write the testbench code to a file (e.g., 'tb.v').
- `simulation_tool`: Run the simulation on the design and testbench files.
- `waveform_tool`: Inspect signals if simulation fails.

Process:
1. Write a self-checking testbench (`tb.v`) for the design (`design.v`).
   - Include `$dumpfile("dump.vcd"); $dumpvars;` in the testbench.
2. Run `simulation_tool` on `['design.v', 'tb.v']`.
3. If it fails, use `waveform_tool` to debug, then report the error.
4. If it passes, say "VERIFICATION PASSED".
"""

def verifier_node(state: DesignState) -> DesignState:
    """
    Agent node that generates testbenches and runs simulations using Tool Calls.
    """
    print("🕵️ Verifier: Verifying design...")
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Design Spec: {state['design_spec']}\nRTL Code has been written to 'design.v'. Please verify it.")
    ]
    
    response = llm_with_tools.invoke(messages)
    messages.append(response)
    
    max_turns = 5
    turn = 0
    
    simulation_passed = False
    error_log = []
    tb_code = ""
    
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
                tb_code = tool_args.get("content", "")

            elif tool_name == "simulation_tool":
                output = simulation_tool.invoke(tool_args)
                if "PASSED" in output:
                    simulation_passed = True
                else:
                    error_log.append(output)

            elif tool_name == "waveform_tool":
                output = waveform_tool.invoke(tool_args)
                error_log.append(f"Waveform Analysis: {output}")

            messages.append(ToolMessage(content=output, tool_call_id=tool_id))

        response = llm_with_tools.invoke(messages)
        messages.append(response)

    return {
        "testbench_code": tb_code,
        "functional_valid": simulation_passed,
        "error_logs": error_log,
        "messages": [AIMessage(content="**Verifier**: " + response.content)]
    }
