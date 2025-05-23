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
        
        # Configure graph with optimizations
        compiled_graph = workflow.compile()
        compiled_graph.config = {
            "batch_requests": True,
            "max_parallel_requests": 1,
            "request_timeout": 30,
            "cache_responses": True,
            "rate_limit": "10/60s"  # 10 requests per minute
        }
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
                    "intermediate_outputs": []
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
                # Validate and chunk data for batch processing
                if not input_state["data_loaded"]:
                    return {
                        "messages": [HumanMessage(content="Data not loaded. Please load data first.")],
                        "output_image_paths": [],
                        "intermediate_outputs": []
                    }

                # Split data into manageable chunks
                chunk_size = min(1000, len(input_state["input_data"]))
                data_chunks = [
                    input_state["input_data"][i:i + chunk_size]
                    for i in range(0, len(input_state["input_data"]), chunk_size)
                ]

                results = []
                for chunk in data_chunks:
                    chunk_state = {
                        **input_state,
                        "input_data": chunk,
                        "is_last_chunk": chunk == data_chunks[-1]
                    }
                    
                    try:
                        result = self.graph.invoke(chunk_state, {
                            "recursion_limit": 15,  # Increased from 8
                            "stop_conditions": {
                                "max_messages": 5,  # Increased from 3
                                "min_response_quality": 0.7,  # Lowered threshold
                                "max_depth": 8,  # Increased from 5
                                "data_available": True,
                                "max_recursion": 15,
                                "early_termination": {
                                    "min_quality_delta": 0.01,
                                    "max_quality_plateau": 3
                                }
                            },
                            "debug": {
                                "log_recursion": True,
                                "log_stop_conditions": True,
                                "log_data_state": True,
                                "log_quality_metrics": True
                            },
                            "retry": {
                                "max_attempts": 3,
                                "delay": 1.0
                            },
                            "recursion": {
                                "track_progress": True,
                                "early_exit": {
                                    "quality_threshold": 0.85,
                                    "max_attempts": 5
                                }
                            }
                        })
                    except Exception as e:
                        if "recursion" in str(e).lower():
                            logger.warning(f"Recursion limit reached, returning partial results: {str(e)}")
                            return {
                                "messages": chunk_state["messages"],
                                "output_image_paths": [],
                                "intermediate_outputs": [],
                                "partial_result": True
                            }
                        raise
                    results.append(result)

                # Combine results from all chunks
                combined_result = {
                    "messages": sum((r["messages"] for r in results), []),
                    "output_image_paths": list(set().union(*(r["output_image_paths"] for r in results))),
                    "intermediate_outputs": sum((r["intermediate_outputs"] for r in results), [])
                }
            except Exception as e:
                logger.error(f"Graph processing error: {str(e)}")
                # Return partial results if available
                if hasattr(e, 'partial_result'):
                    result = e.partial_result
                else:
                    raise
            
            self.chat_history = result["messages"]
            new_image_paths = set(result["output_image_paths"]) - starting_image_paths_set
            self.output_image_paths[len(self.chat_history) - 1] = list(new_image_paths)
            
            if "intermediate_outputs" in result:
                self.intermediate_outputs.extend(result["intermediate_outputs"])
                logger.info(f"Added {len(result['intermediate_outputs'])} intermediate outputs")
                
            duration = time.time() - start_time
            logger.info(f"Successfully processed query in {duration:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise

    def reset_chat(self):
        logger.info("Resetting chat history")
        self.chat_history = []
        self.intermediate_outputs = []
        self.output_image_paths = {}
