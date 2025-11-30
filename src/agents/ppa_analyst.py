import os
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.state.state import DesignState
from src.tools.wrappers import ppa_tool, search_logs_tool
from src.config import DEFAULT_MODEL

# Initialize LLM
if "GOOGLE_API_KEY" not in os.environ:
    from dotenv import load_dotenv
    load_dotenv()

llm = ChatGoogleGenerativeAI(model=DEFAULT_MODEL, google_api_key=os.environ.get("GOOGLE_API_KEY"))

# Bind tools
tools = [ppa_tool, search_logs_tool]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are a PPA Analyst.
Your goal is to extract and analyze Power, Performance, and Area metrics.

Tools:
- `ppa_tool`: Extracts standard metrics (Area, WNS, Power) from the logs.
- `search_logs_tool`: Searches for specific keywords in the logs (e.g., "warning", "violation", "unconstrained").

Process:
1. Call `ppa_tool` to get the baseline metrics.
2. If metrics are missing or suspicious (e.g., zero area), use `search_logs_tool` to investigate errors.
3. Provide a summary report.
"""

def ppa_analyst_node(state: DesignState) -> DesignState:
    """
    Agent node that analyzes PPA using Tool Calls.
    """
    print("📊 PPA Analyst: Analyzing...")
    
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Design Spec: {state['design_spec']}. Synthesis is complete. Please analyze PPA.")
    ]
    
    response = llm_with_tools.invoke(messages)
    messages.append(response)
    
    metrics = {}
    
    max_turns = 5
    turn = 0
    
    while response.tool_calls and turn < max_turns:
        turn += 1
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]

            output = ""
            if tool_name == "ppa_tool":
                output = ppa_tool.invoke(tool_args)
                try:
                    import ast
                    metrics = ast.literal_eval(output)
                except:
                    pass
            elif tool_name == "search_logs_tool":
                output = search_logs_tool.invoke(tool_args)

            messages.append(ToolMessage(content=output, tool_call_id=tool_id))

        response = llm_with_tools.invoke(messages)
        messages.append(response)

    return {
        "ppa_metrics": metrics,
        "messages": [AIMessage(content="**PPA Analyst**: " + response.content)]
    }
