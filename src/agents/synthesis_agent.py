import os
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.state.state import DesignState
from src.tools.wrappers import synthesis_tool
from src.config import DEFAULT_MODEL

# Initialize LLM
if "GOOGLE_API_KEY" not in os.environ:
    from dotenv import load_dotenv
    load_dotenv()

llm = ChatGoogleGenerativeAI(model=DEFAULT_MODEL, google_api_key=os.environ.get("GOOGLE_API_KEY"))

# Bind tools
tools = [synthesis_tool]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are a Synthesis Engineer.
Your goal is to run logic synthesis on the verified design.

Tools:
- `synthesis_tool`: Runs the synthesis flow.

Process:
1. Identify the top module name from the context or assume 'top' if unknown.
2. Call `synthesis_tool` with `design.v` and the top module name.
3. Report the result.
"""

def synthesis_node(state: DesignState) -> DesignState:
    """
    Node to run synthesis using Tool Calls.
    """
    print("🔨 Synthesis Node: Running Synthesis...")
    
    # Simple regex to help the agent find the top module if it wants,
    # but we let the agent figure it out or we provide a hint.
    import re
    match = re.search(r"module\s+(\w+)", state.get("verilog_code", ""))
    top_hint = match.group(1) if match else "unknown"
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Design is ready in 'design.v'. Top module appears to be '{top_hint}'. Run synthesis.")
    ]
    
    response = llm_with_tools.invoke(messages)
    messages.append(response)

    max_turns = 3
    turn = 0
    success = False

    while response.tool_calls and turn < max_turns:
        turn += 1
        for tool_call in response.tool_calls:
            output = synthesis_tool.invoke(tool_call["args"])
            if "Successful" in output:
                success = True
            messages.append(ToolMessage(content=output, tool_call_id=tool_call["id"]))

        response = llm_with_tools.invoke(messages)
        messages.append(response)
        
    return {
        "messages": [AIMessage(content="**Synthesis Agent**: " + response.content)]
    }
