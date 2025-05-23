import logging
import time
from langchain_core.messages import HumanMessage
from typing import List
from dataclasses import dataclass
from langgraph.graph import StateGraph
from Pages.graph.state import AgentState
from Pages.graph.nodes import call_model, call_tools, route_to_tools
from Pages.data_models import InputData

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PythonChatbot:
    def __init__(self):
        super().__init__()
        self.reset_chat()
        self.graph = self.create_graph()
        self.response_cache = set()
        
    def create_graph(self):
        workflow = StateGraph(AgentState)
        workflow.add_node('agent', call_model)
        workflow.add_node('tools', call_tools)

        workflow.add_conditional_edges('agent', route_to_tools)

        workflow.add_edge('tools', 'agent')
        workflow.set_entry_point('agent')
        
        # Configure graph with optimized settings
        compiled_graph = workflow.compile()
        return compiled_graph
    
    def user_sent_message(self, user_query, input_data: List[InputData]):
        logger.info(f"Starting processing for user query: {user_query}")
        start_time = time.time()
        
        try:
            # Validate input data
            if not input_data or len(input_data) == 0:
                return {
                    "messages": [HumanMessage(content="No data available. Please load data first.")],
                    "output_image_paths": [],
                    "intermediate_outputs": [],
                    "token_usage": None
                }

            starting_image_paths_set = set(sum(self.output_image_paths.values(), []))
            input_state = {
                "messages": self.chat_history + [HumanMessage(content=user_query)],
                "output_image_paths": list(starting_image_paths_set),
                "input_data": input_data,
                "data_loaded": bool(input_data and len(input_data) > 0)
            }

            logger.info("Invoking graph with input state")
            try:
                # Validate data loading
                if not input_state["data_loaded"]:
                    return {
                        "messages": [HumanMessage(content="Data not loaded. Please load data first.")],
                        "output_image_paths": [],
                        "intermediate_outputs": [],
                        "token_usage": None
                    }

                # Initialize token usage tracking
                total_token_usage = {
                    "total_tokens": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "estimated_cost": 0.0,
                    "model": "",
                    "requests": 0
                }
                
                try:
                    # Use higher recursion limit with proper error handling
                    result = self.graph.invoke(input_state, {
                        "recursion_limit": 25,  # Increased to handle complex analysis
                        "configurable": {
                            "thread_id": f"session_{int(time.time())}"
                        }
                    })
                    
                    # Accumulate token usage
                    if "token_usage" in result and result["token_usage"]:
                        token_info = result["token_usage"]
                        total_token_usage["total_tokens"] = token_info.get("total_tokens", 0)
                        total_token_usage["prompt_tokens"] = token_info.get("prompt_tokens", 0)
                        total_token_usage["completion_tokens"] = token_info.get("completion_tokens", 0)
                        total_token_usage["estimated_cost"] = token_info.get("estimated_cost", 0.0)
                        total_token_usage["model"] = token_info.get("model", "")
                        total_token_usage["requests"] = 1
                        
                except Exception as e:
                    if "recursion" in str(e).lower():
                        logger.warning(f"Recursion limit reached even with limit 25: {str(e)}")
                        
                        # Create a more helpful response when recursion limit is still hit
                        simplified_response = f"""I understand you want to analyze your data, but the analysis is quite complex and requires many steps. 

**What happened**: The analysis needed more than 25 processing steps, which suggests a very complex query.

**Let me help you break this down**:

1. **Start Simple**: Try these basic questions first:
   - "What does my data look like?" 
   - "Show me the column names and data types"
   - "Display the first 5 rows of my data"

2. **Then Build Up**: Once we see the data structure:
   - "Create a simple chart of [column name]"
   - "Show me basic statistics for [column name]"
   - "What are the unique values in [column name]?"

3. **Advanced Analysis**: After understanding the basics:
   - "Find patterns in [specific columns]"
   - "Compare [column A] vs [column B]"

**Your original question**: "{user_query}"
**Suggestion**: Try breaking this into 2-3 smaller, more specific questions.

Would you like to start with a basic data overview?"""

                        return {
                            "messages": input_state["messages"] + [HumanMessage(content=simplified_response)],
                            "output_image_paths": [],
                            "intermediate_outputs": [f"Recursion limit (25) reached: {str(e)}"],
                            "token_usage": total_token_usage if total_token_usage["requests"] > 0 else None
                        }
                    else:
                        raise

                # Add token usage to result
                if total_token_usage["requests"] > 0:
                    result["token_usage"] = total_token_usage
                
            except Exception as e:
                logger.error(f"Graph processing error: {str(e)}")
                # Return user-friendly error message
                error_response = f"""I encountered an error while analyzing your data: {str(e)}

**Troubleshooting steps**:
1. **Check your data**: Make sure your CSV files are properly formatted
2. **Simplify your question**: Try asking for basic information first
3. **Check file size**: Very large files might cause issues
4. **Try specific columns**: Instead of "analyze everything", ask about specific columns

**Examples of good questions**:
- "Show me the first 10 rows"
- "What columns do I have?"
- "Create a chart of [specific column name]"

You can also check the Debug tab for more technical details."""

                return {
                    "messages": input_state["messages"] + [HumanMessage(content=error_response)],
                    "output_image_paths": [],
                    "intermediate_outputs": [f"Error: {str(e)}"],
                    "token_usage": None
                }
            
            self.chat_history = result["messages"]
            new_image_paths = set(result["output_image_paths"]) - starting_image_paths_set
            self.output_image_paths[len(self.chat_history) - 1] = list(new_image_paths)
            
            if "intermediate_outputs" in result:
                self.intermediate_outputs.extend(result["intermediate_outputs"])
                logger.info(f"Added {len(result['intermediate_outputs'])} intermediate outputs")
            
            # Store token usage for this conversation turn
            if "token_usage" in result and result["token_usage"]:
                self.token_usage_history.append({
                    "timestamp": time.time(),
                    "query": user_query,
                    "usage": result["token_usage"]
                })
                logger.info(f"Token usage: {result['token_usage']}")
                
            duration = time.time() - start_time
            logger.info(f"Successfully processed query in {duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

    def get_total_token_usage(self):
        """Get cumulative token usage for the entire session"""
        if not hasattr(self, 'token_usage_history') or not self.token_usage_history:
            return None
            
        total = {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "estimated_cost": 0.0,
            "total_requests": 0,
            "session_start": min(entry["timestamp"] for entry in self.token_usage_history),
            "last_request": max(entry["timestamp"] for entry in self.token_usage_history)
        }
        
        for entry in self.token_usage_history:
            usage = entry["usage"]
            total["total_tokens"] += usage.get("total_tokens", 0)
            total["prompt_tokens"] += usage.get("prompt_tokens", 0)
            total["completion_tokens"] += usage.get("completion_tokens", 0)
            total["estimated_cost"] += usage.get("estimated_cost", 0.0)
            total["total_requests"] += usage.get("requests", 1)
            
        return total

    def reset_chat(self):
        logger.info("Resetting chat history")
        self.chat_history = []
        self.intermediate_outputs = []
        self.output_image_paths = {}
        self.token_usage_history = []
