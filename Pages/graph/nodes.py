from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, ToolMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.callbacks import BaseCallbackHandler
from .state import AgentState
import json
from typing import Literal, Any, Dict
from .tools import complete_python_task
from langgraph.prebuilt import ToolInvocation, ToolExecutor
import os

# Token usage tracking callback
class TokenUsageCallback(BaseCallbackHandler):
    def __init__(self):
        self.total_tokens = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.cost = 0.0
        
    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        if hasattr(response, 'llm_output') and response.llm_output:
            token_usage = response.llm_output.get('token_usage', {})
            if token_usage:
                self.total_tokens = token_usage.get('total_tokens', 0)
                self.prompt_tokens = token_usage.get('prompt_tokens', 0)
                self.completion_tokens = token_usage.get('completion_tokens', 0)
                
                # Calculate cost based on model (approximate pricing)
                model_name = os.getenv("OPENAI_MODEL", "gpt-4o")
                if "gpt-4o" in model_name:
                    # GPT-4o pricing: $5/1M input, $15/1M output
                    input_cost = (self.prompt_tokens / 1000000) * 5.0
                    output_cost = (self.completion_tokens / 1000000) * 15.0
                    self.cost = input_cost + output_cost
                elif "gpt-4o-mini" in model_name:
                    # GPT-4o-mini pricing: $0.15/1M input, $0.60/1M output
                    input_cost = (self.prompt_tokens / 1000000) * 0.15
                    output_cost = (self.completion_tokens / 1000000) * 0.60
                    self.cost = input_cost + output_cost
                elif "gpt-4-turbo" in model_name:
                    # GPT-4-turbo pricing: $10/1M input, $30/1M output
                    input_cost = (self.prompt_tokens / 1000000) * 10.0
                    output_cost = (self.completion_tokens / 1000000) * 30.0
                    self.cost = input_cost + output_cost
                elif "gpt-3.5-turbo" in model_name:
                    # GPT-3.5-turbo pricing: $0.50/1M input, $1.50/1M output
                    input_cost = (self.prompt_tokens / 1000000) * 0.50
                    output_cost = (self.completion_tokens / 1000000) * 1.50
                    self.cost = input_cost + output_cost

# Load model configuration from environment variables
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0"))

# Initialize callback for token tracking
token_callback = TokenUsageCallback()

llm = ChatOpenAI(
    model=OPENAI_MODEL, 
    temperature=OPENAI_TEMPERATURE,
    callbacks=[token_callback]
)

tools = [complete_python_task]

model = llm.bind_tools(tools)
tool_executor = ToolExecutor(tools)

with open(os.path.join(os.path.dirname(__file__), "../prompts/main_prompt.md"), "r") as file:
    prompt = file.read()

chat_template = ChatPromptTemplate.from_messages([
    ("system", prompt),
    ("placeholder", "{messages}"),
])
model = chat_template | model

def create_data_summary(state: AgentState) -> str:
    summary = ""
    variables = []
    for d in state["input_data"]:
        variables.append(d.variable_name)
        summary += f"\n\nVariable: {d.variable_name}\n"
        summary += f"Description: {d.data_description}"
    
    if "current_variables" in state:
        remaining_variables = [v for v in state["current_variables"] if v not in variables]
        for v in remaining_variables:
            summary += f"\n\nVariable: {v}"
    return summary

def route_to_tools(
    state: AgentState,
) -> Literal["tools", "__end__"]:
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route back to the agent.
    """

    if messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return "__end__"

MAX_TOOL_CALLS = 128

def call_model(state: AgentState):
    # Create data summary
    current_data_template  = """The following data is available:\n{data_summary}"""
    current_data_message = HumanMessage(content=current_data_template.format(data_summary=create_data_summary(state)))
    
    # Prepare messages ensuring we don't exceed context limits
    messages = [current_data_message] + state["messages"]
    if len(messages) > 10:  # Keep last 10 messages
        messages = messages[:10]
    
    # Create limited state
    limited_state = {
        "messages": messages,
        "input_data": state.get("input_data", []),
        "current_variables": state.get("current_variables", [])
    }
    
    # Reset token callback before each call
    global token_callback
    token_callback = TokenUsageCallback()
    
    # Invoke model with limited state and token tracking
    llm_outputs = model.invoke(limited_state, config={"callbacks": [token_callback]})
    
    # Validate tool calls length
    if hasattr(llm_outputs, "tool_calls") and len(llm_outputs.tool_calls) > MAX_TOOL_CALLS:
        raise ValueError(
            f"Too many tool calls generated ({len(llm_outputs.tool_calls)}). "
            f"Maximum allowed is {MAX_TOOL_CALLS}."
        )
    
    # Add token usage information to the response
    token_info = {
        "total_tokens": token_callback.total_tokens,
        "prompt_tokens": token_callback.prompt_tokens,
        "completion_tokens": token_callback.completion_tokens,
        "estimated_cost": round(token_callback.cost, 6),
        "model": OPENAI_MODEL
    }
    
    return {
        "messages": [llm_outputs],
        "intermediate_outputs": [current_data_message.content],
        "token_usage": token_info
    }

def call_tools(state: AgentState):
    last_message = state["messages"][-1]
    tool_invocations = []
    if isinstance(last_message, AIMessage) and hasattr(last_message, 'tool_calls'):
        tool_invocations = [
            ToolInvocation(
                tool=tool_call["name"],
                tool_input={**tool_call["args"], "graph_state": state}
            ) for tool_call in last_message.tool_calls
        ]

    responses = tool_executor.batch(tool_invocations, return_exceptions=True)
    tool_messages = []
    state_updates = {}

    for tc, response in zip(last_message.tool_calls, responses):
        if isinstance(response, Exception):
            raise response
        message, updates = response
        tool_messages.append(ToolMessage(
            content=str(message),
            name=tc["name"],
            tool_call_id=tc["id"]
        ))
        state_updates.update(updates)

    if 'messages' not in state_updates:
        state_updates["messages"] = []

    state_updates["messages"] = tool_messages 
    return state_updates
