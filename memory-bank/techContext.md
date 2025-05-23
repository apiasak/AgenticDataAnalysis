# Technical Context - Agentic Data Analysis

## Technology Stack

### Core Framework
- **LangGraph**: Agent orchestration and state management
- **LangChain**: LLM integration and tool abstractions
- **Streamlit**: Web interface and user interaction
- **OpenAI GPT-4o**: Language model for reasoning and code generation

### Data Processing
- **Pandas**: Data manipulation and analysis
- **Scikit-learn**: Machine learning algorithms
- **Plotly**: Interactive visualization generation

### Development Environment
- **Python 3.x**: Primary development language
- **JSON**: Configuration and data serialization
- **Pickle**: Complex object persistence fallback

## Dependencies

### Core Requirements (`requirements.txt`)
```
pandas              # Data manipulation
streamlit           # Web interface
langchain-core      # LLM abstractions
scikit-learn        # Machine learning
plotly              # Visualization
langchain           # Agent framework
langgraph           # State graph orchestration
langchain-openai    # OpenAI integration
```

### System Dependencies
- **Python 3.8+**: Required for LangGraph compatibility
- **OpenAI API Key**: Required for GPT-4o access
- **File System Access**: Local storage for uploads and outputs

## Development Setup

### Environment Configuration
```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key (production)
export OPENAI_API_KEY="your-api-key-here"

# Run application
streamlit run data_analysis_streamlit_app.py --server.maxUploadSize 2000
```

### Directory Structure
```
AgenticDataAnalysis/
├── data_analysis_streamlit_app.py    # Main application entry
├── requirements.txt                   # Python dependencies
├── data_dictionary.json              # Dataset metadata
├── README.md                         # Project documentation
├── memory-bank/                      # Documentation (this system)
├── Pages/                            # Application modules
│   ├── __init__.py
│   ├── backend.py                    # Core agent logic
│   ├── data_models.py               # Data structures
│   ├── python_visualisation_agent.py # Main UI page
│   ├── graph/                       # LangGraph components
│   │   ├── nodes.py                 # Agent nodes
│   │   ├── state.py                 # State definitions
│   │   └── tools.py                 # Tool implementations
│   └── prompts/                     # System prompts
│       └── main_prompt.md           # Agent instructions
├── uploads/                         # User-uploaded CSV files
└── images/                          # Generated visualizations
    └── plotly_figures/
        └── pickle/                  # Stored figure files
```

## Technical Constraints

### Performance Limitations
- **Single-threaded Execution**: Python REPL runs sequentially
- **Memory Constraints**: Large datasets may cause memory issues
- **API Rate Limits**: OpenAI API has usage quotas
- **Session Persistence**: Variables only persist within single session

### Security Restrictions
- **Sandboxed Execution**: Limited library imports for security
- **File System Access**: Restricted to designated directories
- **Network Isolation**: No external network calls from Python code
- **Code Injection**: Input sanitization prevents malicious code

### Scalability Constraints
- **Single User**: No multi-user session management
- **Local Storage**: Files stored locally, not in cloud
- **Synchronous Processing**: No async/parallel execution
- **Memory Persistence**: No cross-session state preservation

## Configuration Management

### Application Settings
```python
# Streamlit configuration
st.set_page_config(layout="wide", page_title="Main Dashboard", page_icon="📊")

# Upload size limit
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = "2000"  # 2GB

# OpenAI API configuration
os.environ["OPENAI_API_KEY"] = "your-key-here"
```

### LangGraph Configuration
```python
# Graph compilation settings
compiled_graph.config = {
    "batch_requests": True,
    "max_parallel_requests": 1,
    "request_timeout": 30,
    "cache_responses": True,
    "rate_limit": "10/60s"
}

# Execution limits
{
    "recursion_limit": 15,
    "stop_conditions": {
        "max_messages": 5,
        "min_response_quality": 0.7,
        "max_depth": 8
    }
}
```

## Data Models

### Core Data Structures
```python
@dataclass
class InputData:
    variable_name: str      # Python variable name for dataset
    data_path: str         # Absolute path to CSV file
    data_description: str  # User-provided description

class AgentState(TypedDict):
    messages: List[BaseMessage]           # Conversation history
    input_data: List[InputData]          # Available datasets
    output_image_paths: List[str]        # Generated visualizations
    intermediate_outputs: List[dict]     # Debug information
    current_variables: dict              # Python execution state
    data_loaded: bool                    # Data availability flag
```

### Data Dictionary Schema
```json
{
    "filename.csv": {
        "description": "Dataset description",
        "coverage": "Data coverage information",
        "features": ["list", "of", "key", "features"],
        "usage": "Intended use cases",
        "linkage": "Relationship to other datasets"
    }
}
```

## Integration Points

### OpenAI API Integration
```python
# Model configuration
llm = ChatOpenAI(model="gpt-4o", temperature=0)
model = llm.bind_tools(tools)

# Prompt template
chat_template = ChatPromptTemplate.from_messages([
    ("system", prompt),
    ("placeholder", "{messages}"),
])
```

### Streamlit Integration
```python
# Session state management
if 'visualisation_chatbot' not in st.session_state:
    st.session_state.visualisation_chatbot = PythonChatbot()

# File upload handling
uploaded_files = st.file_uploader("Upload CSV files", type="csv", accept_multiple_files=True)

# Chat interface
st.chat_input(placeholder="Ask me anything about your data", on_submit=on_submit_user_query)
```

### File System Integration
```python
# Upload directory management
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Visualization storage
if not os.path.exists("images/plotly_figures/pickle"):
    os.makedirs("images/plotly_figures/pickle")
```

## Development Patterns

### Error Handling Strategy
```python
# Graceful degradation
try:
    result = self.graph.invoke(chunk_state, config)
except Exception as e:
    if "recursion" in str(e).lower():
        logger.warning(f"Recursion limit reached: {str(e)}")
        return partial_results
    raise
```

### Logging Implementation
```python
# Structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)
logger.info(f"Starting processing for user query: {user_query}")
```

### State Management Pattern
```python
# Immutable state updates
def call_model(state: AgentState):
    # Process state
    llm_outputs = model.invoke(limited_state)
    
    # Return updates, don't mutate
    return {
        "messages": [llm_outputs],
        "intermediate_outputs": [current_data_message.content]
    }
```

## Testing Considerations

### Manual Testing Workflow
1. **Upload Test Data**: Use sample CSV files
2. **Basic Queries**: Test simple analysis requests
3. **Complex Analysis**: Multi-step data exploration
4. **Error Scenarios**: Invalid data, malformed queries
5. **Visualization**: Verify chart generation and display

### Key Test Cases
- **Data Loading**: Various CSV formats and sizes
- **Query Processing**: Natural language understanding
- **Code Execution**: Python analysis correctness
- **Visualization**: Chart generation and storage
- **Error Handling**: Graceful failure scenarios

## Deployment Considerations

### Local Development
```bash
# Development server
streamlit run data_analysis_streamlit_app.py --server.maxUploadSize 2000

# Debug mode
streamlit run data_analysis_streamlit_app.py --logger.level debug
```

### Production Deployment
- **Environment Variables**: Secure API key management
- **Resource Limits**: Memory and CPU constraints
- **File Storage**: Persistent storage for uploads
- **Monitoring**: Application health and performance
- **Security**: Input validation and sandboxing

### Performance Optimization
- **Caching**: Response and computation caching
- **Chunking**: Large dataset processing
- **Async**: Non-blocking operations where possible
- **Resource Management**: Memory cleanup and limits

## Future Technical Enhancements

### Near-term Improvements
- **Database Integration**: Replace file-based storage
- **Async Processing**: Non-blocking analysis execution
- **Enhanced Security**: Improved sandboxing and validation
- **Performance Monitoring**: Metrics and alerting

### Long-term Architecture Evolution
- **Microservices**: Separate analysis and UI services
- **Cloud Deployment**: Scalable cloud infrastructure
- **Multi-user Support**: Session isolation and management
- **Real-time Data**: Streaming data integration
