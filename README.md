# Agentic Data Analysis

This is an AI agent built in LangGraph that can perform data analysis on a provided dataset. It is to accompany my Youtube video to showcase some advanced LangGraph techniques.

Take a look at the below video for a demo:



https://github.com/user-attachments/assets/83bdc543-85ca-49c0-83a5-39d948f74286



## Getting Setup

If you want to use the same dataset as me, you can download it from Kaggle below:

https://www.kaggle.com/datasets/computingvictor/transactions-fraud-datasets/data 

Otherwise feel free to upload your own dataset!

## Setup Instructions

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   - Copy the example environment file:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your OpenAI API key:
     ```
     OPENAI_API_KEY=your_actual_api_key_here
     ```
   - Get your API key from: https://platform.openai.com/api-keys

3. **Run the Application**
   ```bash
   streamlit run data_analysis_streamlit_app.py --server.maxUploadSize 2000
   ```

Enjoy!
