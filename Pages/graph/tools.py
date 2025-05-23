from langchain_core.tools import tool
from langchain_core.messages import AIMessage
from typing import Annotated, Tuple
from langgraph.prebuilt import InjectedState
import sys
from io import StringIO
import os
import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
import pandas as pd
import sklearn
import traceback

persistent_vars = {}
plotly_saving_code = """import pickle
import json
import uuid
import plotly
import pandas as pd
import plotly.io as pio

def convert_periods(obj):
    if isinstance(obj, pd.Period):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_periods(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_periods(x) for x in obj]
    return obj

for figure in plotly_figures:
    # Try JSON serialization first
    try:
        # Convert figure to JSON using plotly's built-in function
        figure_json = pio.to_json(figure)
        json_filename = f"images/plotly_figures/pickle/{uuid.uuid4()}.json"
        with open(json_filename, 'w') as f:
            f.write(figure_json)
    except Exception as json_error:
        # Fall back to pickle if JSON fails
        figure = convert_periods(figure)
        pickle_filename = f"images/plotly_figures/pickle/{uuid.uuid4()}.pickle"
        with open(pickle_filename, 'wb') as f:
            pickle.dump(figure, f)
"""

def get_user_friendly_error(error_str, code):
    """Convert technical errors to user-friendly messages"""
    error_lower = error_str.lower()
    
    if "nameerror" in error_lower:
        if "dataset" in error_lower:
            return "❌ Dataset not found. Make sure you've uploaded and selected your data files."
        else:
            return "❌ Variable not found. This might happen if you're referencing something that wasn't created yet."
    
    elif "keyerror" in error_lower:
        return "❌ Column not found in the dataset. Please check the column names in your data."
    
    elif "indexerror" in error_lower:
        return "❌ Index out of range. This usually means trying to access data that doesn't exist."
    
    elif "valueerror" in error_lower:
        if "empty" in error_lower:
            return "❌ No data to analyze. Please check that your dataset contains data."
        else:
            return "❌ Invalid data values. Please check your data format and try again."
    
    elif "typeerror" in error_lower:
        return "❌ Data type mismatch. This often happens when trying to perform operations on incompatible data types."
    
    elif "memoryerror" in error_lower:
        return "💾 Dataset too large for analysis. Try working with a smaller subset of your data."
    
    elif "syntaxerror" in error_lower:
        return "🔧 Code syntax error. The AI generated invalid Python code - please try rephrasing your question."
    
    elif "importerror" in error_lower or "modulenotfounderror" in error_lower:
        return "📦 Missing required library. Some advanced features may not be available."
    
    else:
        return f"❌ Analysis error: {error_str[:100]}{'...' if len(error_str) > 100 else ''}"

@tool(parse_docstring=True)
def complete_python_task(
        graph_state: Annotated[dict, InjectedState], thought: str, python_code: str
) -> Tuple[str, dict]:
    """Completes a python task

    Args:
        thought: Internal thought about the next action to be taken, and the reasoning behind it. This should be formatted in MARKDOWN and be high quality.
        python_code: Python code to be executed to perform analyses, create a new dataset or create a visualization.
    """
    current_variables = graph_state["current_variables"] if "current_variables" in graph_state else {}
    
    # Load all datasets with automatic naming
    datasets = []
    for input_dataset in graph_state["input_data"]:
        try:
            df = pd.read_csv(input_dataset.data_path)
            var_name = f"dataset_{len(datasets)}"
            current_variables[var_name] = df
            datasets.append({
                'name': var_name,
                'data': df,
                'size': len(df),
                'types': df.dtypes.to_dict(),
                'sample': df.head(1).to_dict(orient='records')[0] if len(df) > 0 else {}
            })
        except Exception as e:
            error_msg = get_user_friendly_error(str(e), "")
            return f"Error loading dataset: {error_msg}", {
                "intermediate_outputs": [{
                    "error": f"Failed to load dataset {input_dataset.data_path}",
                    "details": str(e),
                    "user_friendly": error_msg
                }]
            }
    
    # Create generic relationships between datasets
    if len(datasets) > 1:
        try:
            # Create combined views based on data patterns
            numeric_cols = {}
            date_cols = {}
            
            for ds in datasets:
                for col, dtype in ds['types'].items():
                    if 'float' in str(dtype) or 'int' in str(dtype):
                        numeric_cols.setdefault('numeric', []).append(f"{ds['name']}.{col}")
                    if 'datetime' in str(dtype) or 'date' in str(dtype):
                        date_cols.setdefault('date', []).append(f"{ds['name']}.{col}")
            
            # Store relationship metadata
            current_variables["_metadata"] = {
                'datasets': datasets,
                'relationships': {
                    'numeric_columns': numeric_cols,
                    'date_columns': date_cols
                }
            }
            
        except Exception as e:
            error_msg = get_user_friendly_error(str(e), "")
            return f"Error creating dataset relationships: {error_msg}", {
                "intermediate_outputs": [{
                    "error": "Failed to create dataset relationships",
                    "details": str(e),
                    "user_friendly": error_msg
                }]
            }
    
    if not os.path.exists("images/plotly_figures/pickle"):
        os.makedirs("images/plotly_figures/pickle")

    current_image_pickle_files = os.listdir("images/plotly_figures/pickle")
    old_stdout = None
    
    try:
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        # Execute the code and capture the result
        exec_globals = globals().copy()
        exec_globals.update(persistent_vars)
        exec_globals.update(current_variables)
        exec_globals.update({"plotly_figures": []})

        # Add safety checks for common issues
        if "dataset_" not in python_code and len(datasets) > 0:
            # If no dataset is referenced, add a helpful comment
            python_code = f"# Available datasets: {', '.join([ds['name'] for ds in datasets])}\n" + python_code

        exec(python_code, exec_globals)
        persistent_vars.update({k: v for k, v in exec_globals.items() if k not in globals()})

        # Get the captured stdout
        output = sys.stdout.getvalue()

        # Restore stdout
        sys.stdout = old_stdout

        updated_state = {
            "intermediate_outputs": [{"thought": thought, "code": python_code, "output": output}],
            "current_variables": persistent_vars
        }

        if 'plotly_figures' in exec_globals and exec_globals['plotly_figures']:
            try:
                exec(plotly_saving_code, exec_globals)
                # Check if any images were created
                new_image_folder_contents = os.listdir("images/plotly_figures/pickle")
                new_image_files = [file for file in new_image_folder_contents if file not in current_image_pickle_files]
                if new_image_files:
                    updated_state["output_image_paths"] = new_image_files
                
                persistent_vars["plotly_figures"] = []
            except Exception as plot_error:
                # Don't fail the entire operation if plotting fails
                output += f"\n⚠️ Warning: Could not save visualization: {str(plot_error)}"
                updated_state["intermediate_outputs"][0]["output"] = output

        return output, updated_state
        
    except Exception as e:
        # Restore stdout if it was captured
        if old_stdout:
            sys.stdout = old_stdout
        
        # Get detailed error information
        error_details = traceback.format_exc()
        error_msg = get_user_friendly_error(str(e), python_code)
        
        # Provide helpful suggestions based on error type
        suggestions = []
        if "NameError" in str(e):
            suggestions.append("💡 Try describing your data first with: 'Show me a summary of my data'")
        elif "KeyError" in str(e):
            suggestions.append("💡 Check available columns with: 'What columns are in my dataset?'")
        elif "ValueError" in str(e) and "empty" in str(e).lower():
            suggestions.append("💡 Your dataset might be empty. Try uploading data first.")
        
        suggestion_text = "\n".join(suggestions) if suggestions else ""
        
        return f"{error_msg}\n{suggestion_text}", {
            "intermediate_outputs": [{
                "thought": thought, 
                "code": python_code, 
                "output": error_msg,
                "error_details": error_details,
                "suggestions": suggestions
            }]
        }
