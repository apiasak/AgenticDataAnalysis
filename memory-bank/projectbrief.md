# Agentic Data Analysis - Project Brief

## Project Overview
An AI-powered data analysis system built with LangGraph that provides intelligent, conversational data analysis through a Streamlit web interface. The system acts as a professional data scientist assistant, helping non-technical users understand, analyze, and visualize their datasets.

## Core Purpose
Transform complex data analysis into an accessible, conversational experience where users can:
- Upload CSV datasets and get immediate insights
- Ask natural language questions about their data
- Receive professional-grade visualizations and analysis
- Iterate through data exploration with AI guidance

## Primary Use Case
**Financial Transaction Analysis & Fraud Detection**
- Designed around financial datasets (transactions, cards, users, MCC codes)
- Fraud detection model training and evaluation
- Customer segmentation and spending pattern analysis
- Risk assessment and anomaly detection

## Key Features

### 1. Intelligent Agent System
- LangGraph-powered AI agent with persistent memory
- Iterative analysis with user feedback loops
- Professional data scientist reasoning and methodology

### 2. Multi-Modal Interface
- **Data Management**: Upload, preview, and describe datasets
- **Chat Interface**: Natural language data analysis conversations
- **Debug View**: Transparent intermediate outputs and code execution

### 3. Advanced Visualization
- Plotly-based interactive charts and graphs
- Automatic figure generation and persistence
- JSON/pickle hybrid storage for reliability

### 4. Persistent Analysis Environment
- Variables persist between analysis steps
- Iterative data exploration and refinement
- Cumulative knowledge building within sessions

## Technical Foundation
- **Backend**: LangGraph StateGraph with OpenAI GPT-4o
- **Frontend**: Streamlit multi-page application
- **Execution**: Sandboxed Python environment with scientific libraries
- **Storage**: Local file system with organized asset management

## Success Metrics
1. **User Experience**: Non-technical users can perform sophisticated analysis
2. **Analysis Quality**: Professional-grade insights and visualizations
3. **Iteration Speed**: Rapid exploration and refinement cycles
4. **Transparency**: Clear reasoning and reproducible results

## Target Audience
- Business analysts working with financial data
- Risk management teams
- Data-curious professionals without deep technical skills
- Anyone needing quick, intelligent data insights

## Project Scope
**In Scope:**
- CSV data upload and analysis
- Natural language query processing
- Interactive visualization generation
- Fraud detection and financial analysis
- User-guided iterative exploration

**Out of Scope:**
- Real-time data streaming
- Database integrations
- Multi-user collaboration
- Production-scale deployment features

## Key Constraints
- OpenAI API dependency for intelligence
- Local execution environment
- CSV-only data input format
- Single-session persistence (no cross-session memory)
