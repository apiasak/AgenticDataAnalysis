import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables from .env file
load_dotenv()

# Set configuration from environment variables
os.environ["STREAMLIT_SERVER_MAX_UPLOAD_SIZE"] = os.getenv("STREAMLIT_SERVER_MAX_UPLOAD_SIZE", "2000")

# Verify OpenAI API key is loaded
if not os.getenv("OPENAI_API_KEY"):
    st.error("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
    st.stop()

# Set Streamlit to wide mode
st.set_page_config(layout="wide", page_title="Main Dashboard", page_icon="📊")


data_visualisation_page = st.Page(
    "./Pages/python_visualisation_agent.py", title="Data Visualisation", icon="📈"
)

pg = st.navigation(
    {
        "Visualisation Agent": [data_visualisation_page]
    }
)

pg.run()
