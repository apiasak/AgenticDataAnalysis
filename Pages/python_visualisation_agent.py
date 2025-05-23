import streamlit as st
import pandas as pd
import os
import json
from langchain_core.messages import HumanMessage, AIMessage
from Pages.backend import PythonChatbot, InputData
import pickle
import plotly.io as pio
from datetime import datetime

# Create uploads directory if it doesn't exist
if not os.path.exists("uploads"):
    os.makedirs("uploads")

st.title("Data Analysis Dashboard")

# Load data dictionary
with open('data_dictionary.json', 'r') as f:
    data_dictionary = json.load(f)

tab1, tab2, tab3, tab4 = st.tabs(["Data Management", "Chat Interface", "Debug", "Token Usage"])

with tab1:
    # File upload section
    uploaded_files = st.file_uploader("Upload CSV files", type="csv", accept_multiple_files=True)

    if uploaded_files:
        # Save uploaded files
        for file in uploaded_files:
            with open(os.path.join("uploads", file.name), "wb") as f:
                f.write(file.getbuffer())
        st.success("Files uploaded successfully!")

    # Get list of available CSV files
    available_files = [f for f in os.listdir("uploads") if f.endswith('.csv')]

    if available_files:
        # File selection
        selected_files = st.multiselect(
            "Select files to analyze",
            available_files,
            key="selected_files"
        )
        
        # Dictionary to store new descriptions
        new_descriptions = {}
        
        if selected_files:
            # Create tabs for each selected file
            file_tabs = st.tabs(selected_files)
            
            # Display dataframe previews and data dictionary info in tabs
            for tab, filename in zip(file_tabs, selected_files):
                with tab:
                    try:
                        df = pd.read_csv(os.path.join("uploads", filename))
                        st.write(f"Preview of {filename}:")
                        st.dataframe(df.head())
                        
                        # Display/edit data dictionary information
                        st.subheader("Dataset Information")
                        
                        if filename in data_dictionary:
                            info = data_dictionary[filename]
                            current_description = info.get('description', '')
                        else:
                            current_description = ''
                            
                        new_descriptions[filename] = st.text_area(
                            "Dataset Description",
                            value=current_description,
                            key=f"description_{filename}",
                            help="Provide a description of this dataset"
                        )
                        
                        if filename in data_dictionary:
                            info = data_dictionary[filename]
                            
                            if 'coverage' in info:
                                st.write(f"**Coverage:** {info['coverage']}")
                                
                            if 'features' in info:
                                st.write("**Features:**")
                                for feature in info['features']:
                                    st.write(f"- {feature}")
                                    
                            if 'usage' in info:
                                st.write("**Usage:**")
                                if isinstance(info['usage'], list):
                                    for use in info['usage']:
                                        st.write(f"- {use}")
                                else:
                                    st.write(f"- {info['usage']}")
                                    
                            if 'linkage' in info:
                                st.write(f"**Linkage:** {info['linkage']}")
                                
                    except Exception as e:
                        st.error(f"Error loading {filename}: {str(e)}")
            
            # Save button for descriptions
            if st.button("Save Descriptions"):
                for filename, description in new_descriptions.items():
                    if description:  # Only update if description is not empty
                        if filename not in data_dictionary:
                            data_dictionary[filename] = {}
                        data_dictionary[filename]['description'] = description
                
                # Save updated data dictionary
                with open('data_dictionary.json', 'w') as f:
                    json.dump(data_dictionary, f, indent=4)
                st.success("Descriptions saved successfully!")
                
    else:
        st.info("No CSV files available. Please upload some files first.")

with tab2:
    def process_user_query(user_query):
        """Process user query with progress indicators and error handling"""
        if 'selected_files' not in st.session_state or not st.session_state['selected_files']:
            st.error("Please select files to analyze in the Data Management tab first.")
            return
            
        input_data_list = [
            InputData(
                variable_name=f"{file.split('.')[0]}", 
                data_path=os.path.abspath(os.path.join("uploads", file)), 
                data_description=data_dictionary.get(file, {}).get('description', '')
            ) 
            for file in st.session_state['selected_files']
        ]
        
        # Show progress indicator
        with st.spinner("🤖 Analyzing your data..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔍 Processing your query...")
                progress_bar.progress(25)
                
                status_text.text("🧠 AI is thinking...")
                progress_bar.progress(50)
                
                status_text.text("📊 Generating analysis...")
                progress_bar.progress(75)
                
                st.session_state.visualisation_chatbot.user_sent_message(user_query, input_data=input_data_list)
                
                progress_bar.progress(100)
                status_text.text("✅ Analysis complete!")
                
                # Clear progress indicators after a brief moment
                import time
                time.sleep(0.5)
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                
                # User-friendly error handling
                error_message = str(e)
                if "recursion" in error_message.lower():
                    st.error("🔄 The analysis became too complex. Try asking a simpler question or breaking it into smaller parts.")
                elif "openai" in error_message.lower() or "api" in error_message.lower():
                    st.error("🔑 There's an issue with the AI service. Please check your API key configuration.")
                elif "memory" in error_message.lower() or "size" in error_message.lower():
                    st.error("💾 Your dataset might be too large. Try analyzing a smaller subset of your data.")
                elif "pandas" in error_message.lower() or "dataframe" in error_message.lower():
                    st.error("📊 There's an issue with your data format. Please check that your CSV files are properly formatted.")
                else:
                    st.error("❌ Something went wrong with the analysis. Please try rephrasing your question.")
                
                # Show technical details in an expandable section
                with st.expander("🔧 Technical Details (for debugging)"):
                    st.code(error_message)
                    st.write("**Suggestion:** Try asking a simpler question or check the Debug tab for more information.")

    def generate_smart_suggestions(selected_files):
        """Generate contextual query suggestions based on uploaded files"""
        suggestions = []
        
        # Basic exploration suggestions
        suggestions.extend([
            "📊 Show me a summary of my data",
            "🔍 What are the main patterns in this dataset?",
            "📈 Create visualizations to explore the data"
        ])
        
        # File-specific suggestions
        for filename in selected_files:
            file_lower = filename.lower()
            if 'transaction' in file_lower or 'payment' in file_lower:
                suggestions.extend([
                    "💳 Analyze transaction patterns and trends",
                    "🚨 Detect any fraudulent or unusual transactions",
                    "💰 Show spending patterns by category"
                ])
            elif 'customer' in file_lower or 'user' in file_lower:
                suggestions.extend([
                    "👥 Segment customers based on behavior",
                    "📊 Show customer demographics breakdown",
                    "🎯 Identify high-value customers"
                ])
            elif 'sales' in file_lower:
                suggestions.extend([
                    "📈 Show sales trends over time",
                    "🏆 Identify top performing products",
                    "📊 Analyze seasonal patterns"
                ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for suggestion in suggestions:
            if suggestion not in seen:
                seen.add(suggestion)
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:6]  # Limit to 6 suggestions

    if 'selected_files' in st.session_state and st.session_state['selected_files']:
        if 'visualisation_chatbot' not in st.session_state:
            st.session_state.visualisation_chatbot = PythonChatbot()
        
        # Smart Query Suggestions
        if len(st.session_state.visualisation_chatbot.chat_history) == 0:
            st.subheader("💡 Smart Suggestions")
            st.write("Get started with these suggested questions:")
            
            suggestions = generate_smart_suggestions(st.session_state['selected_files'])
            
            # Create columns for suggestions
            cols = st.columns(2)
            for i, suggestion in enumerate(suggestions):
                with cols[i % 2]:
                    if st.button(suggestion, key=f"suggestion_{i}", use_container_width=True):
                        # Process the suggestion directly
                        process_user_query(suggestion)
                        st.rerun()
            
            st.divider()
        
        chat_container = st.container(height=500)
        with chat_container:
            # Display chat history with associated images
            for msg_index, msg in enumerate(st.session_state.visualisation_chatbot.chat_history):
                msg_col, img_col = st.columns([2, 1])
                
                with msg_col:
                    if isinstance(msg, HumanMessage):
                        st.chat_message("You").markdown(msg.content)
                    elif isinstance(msg, AIMessage):
                        with st.chat_message("AI"):
                            st.markdown(msg.content)

                    if isinstance(msg, AIMessage) and msg_index in st.session_state.visualisation_chatbot.output_image_paths:
                        image_paths = st.session_state.visualisation_chatbot.output_image_paths[msg_index]
                        for image_path in image_paths:
                            try:
                                if image_path.endswith('.json'):
                                    with open(os.path.join("images/plotly_figures/pickle", image_path), "r") as f:
                                        fig_json = f.read()
                                        fig = pio.from_json(fig_json)
                                else:
                                    with open(os.path.join("images/plotly_figures/pickle", image_path), "rb") as f:
                                        fig = pickle.load(f)
                                st.plotly_chart(fig, use_container_width=True)
                            except Exception as e:
                                st.error(f"Error displaying chart: {str(e)}")
        
        # Chat input - using callback function instead of session state assignment
        user_input = st.chat_input(placeholder="Ask me anything about your data")
        if user_input:
            process_user_query(user_input)
            st.rerun()
            
    else:
        st.info("Please select files to analyze in the Data Management tab first.")

with tab3:
    if 'visualisation_chatbot' in st.session_state:
        st.subheader("Intermediate Outputs")
        for i, output in enumerate(st.session_state.visualisation_chatbot.intermediate_outputs):
            with st.expander(f"Step {i+1}"):
                if isinstance(output, dict):
                    if 'thought' in output:
                        st.markdown("### Thought Process")
                        st.markdown(output['thought'])
                    if 'code' in output:
                        st.markdown("### Code")
                        st.code(output['code'], language="python")
                    if 'output' in output:
                        st.markdown("### Output")
                        st.text(output['output'])
                else:
                    st.markdown("### Output")
                    st.text(str(output))
    else:
        st.info("No debug information available yet. Start a conversation to see intermediate outputs.")

with tab4:
    st.subheader("🔢 Token Usage Analytics")
    
    if 'visualisation_chatbot' in st.session_state:
        # Get total session usage
        total_usage = st.session_state.visualisation_chatbot.get_total_token_usage()
        
        if total_usage:
            # Display session summary
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Total Tokens",
                    value=f"{total_usage['total_tokens']:,}",
                    help="Total tokens used in this session"
                )
            
            with col2:
                st.metric(
                    label="Input Tokens",
                    value=f"{total_usage['prompt_tokens']:,}",
                    help="Tokens used for input/prompts"
                )
            
            with col3:
                st.metric(
                    label="Output Tokens", 
                    value=f"{total_usage['completion_tokens']:,}",
                    help="Tokens used for AI responses"
                )
            
            with col4:
                st.metric(
                    label="Estimated Cost",
                    value=f"${total_usage['estimated_cost']:.4f}",
                    help="Estimated cost based on current pricing"
                )
            
            # Additional session info
            st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Total Requests:** {total_usage['total_requests']}")
                session_duration = total_usage['last_request'] - total_usage['session_start']
                st.write(f"**Session Duration:** {session_duration/60:.1f} minutes")
            
            with col2:
                avg_tokens_per_request = total_usage['total_tokens'] / total_usage['total_requests']
                st.write(f"**Avg Tokens/Request:** {avg_tokens_per_request:.0f}")
                avg_cost_per_request = total_usage['estimated_cost'] / total_usage['total_requests']
                st.write(f"**Avg Cost/Request:** ${avg_cost_per_request:.4f}")
            
            # Detailed usage history
            st.subheader("📊 Usage History")
            
            if hasattr(st.session_state.visualisation_chatbot, 'token_usage_history'):
                usage_data = []
                for i, entry in enumerate(st.session_state.visualisation_chatbot.token_usage_history):
                    usage_data.append({
                        "Request": i + 1,
                        "Query": entry['query'][:50] + "..." if len(entry['query']) > 50 else entry['query'],
                        "Total Tokens": entry['usage']['total_tokens'],
                        "Input Tokens": entry['usage']['prompt_tokens'],
                        "Output Tokens": entry['usage']['completion_tokens'],
                        "Cost ($)": f"{entry['usage']['estimated_cost']:.4f}",
                        "Time": datetime.fromtimestamp(entry['timestamp']).strftime("%H:%M:%S")
                    })
                
                if usage_data:
                    df_usage = pd.DataFrame(usage_data)
                    st.dataframe(df_usage, use_container_width=True)
                    
                    # Token usage chart
                    st.subheader("📈 Token Usage Trend")
                    
                    import plotly.express as px
                    fig = px.line(
                        df_usage, 
                        x="Request", 
                        y="Total Tokens",
                        title="Token Usage per Request",
                        markers=True
                    )
                    fig.update_layout(
                        xaxis_title="Request Number",
                        yaxis_title="Total Tokens",
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Cost breakdown chart
                    st.subheader("💰 Cost Breakdown")
                    
                    cost_data = pd.DataFrame({
                        "Type": ["Input Tokens", "Output Tokens"],
                        "Tokens": [total_usage['prompt_tokens'], total_usage['completion_tokens']],
                        "Cost": [
                            (total_usage['prompt_tokens'] / 1000000) * (5.0 if "gpt-4o" in os.getenv("OPENAI_MODEL", "gpt-4o") else 0.15),
                            (total_usage['completion_tokens'] / 1000000) * (15.0 if "gpt-4o" in os.getenv("OPENAI_MODEL", "gpt-4o") else 0.60)
                        ]
                    })
                    
                    fig_cost = px.pie(
                        cost_data,
                        values="Cost",
                        names="Type", 
                        title="Cost Distribution by Token Type"
                    )
                    st.plotly_chart(fig_cost, use_container_width=True)
                    
                    # Model info
                    st.info(f"**Current Model:** {os.getenv('OPENAI_MODEL', 'gpt-4o')} | **Temperature:** {os.getenv('OPENAI_TEMPERATURE', '0')}")
                    
        else:
            st.info("No token usage data available yet. Start a conversation to see usage analytics.")
            
        # Reset button
        if st.button("🔄 Reset Token Usage History", type="secondary"):
            if hasattr(st.session_state.visualisation_chatbot, 'token_usage_history'):
                st.session_state.visualisation_chatbot.token_usage_history = []
                st.success("Token usage history reset!")
                st.rerun()
                
    else:
        st.info("Start a conversation to see token usage analytics.")
