import os
import json
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.state.state import DesignState
from src.tools.wrappers import ppa_tool
from src.config import DEFAULT_MODEL

# Initialize LLM
if "GOOGLE_API_KEY" not in os.environ:
    from dotenv import load_dotenv
    load_dotenv()

llm = ChatGoogleGenerativeAI(model=DEFAULT_MODEL, google_api_key=os.environ.get("GOOGLE_API_KEY"))

# Bind tools
tools = [ppa_tool]
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are a PPA Analyst.
Your goal is to extract and analyze Power, Performance, and Area metrics.

Tools:
- `ppa_tool`: Extracts metrics from the logs.

Process:
1. Call `ppa_tool`.
2. Analyze the returned JSON metrics against the design spec.
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
    
    max_turns = 3
    turn = 0
    
    while response.tool_calls and turn < max_turns:
        turn += 1
        for tool_call in response.tool_calls:
            output = ppa_tool.invoke(tool_call["args"])
            try:
                # ppa_tool returns a string repr of a dict
                # We try to parse it safely if we want to store it in state['ppa_metrics']
                # But ppa_tool output might be just a string.
                # Let's trust ast.literal_eval or json if strict.
                import ast
                metrics = ast.literal_eval(output)
            except:
                pass
            messages.append(ToolMessage(content=output, tool_call_id=tool_call["id"]))

        response = llm_with_tools.invoke(messages)
        messages.append(response)

    return {
        "ppa_metrics": metrics,
        "messages": [AIMessage(content="**PPA Analyst**: " + response.content)]
    }
