import streamlit as st
import os
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from agent import SQLAgent

st.set_page_config(page_title="NL-to-SQL Agent", page_icon="🤖", layout="wide")

# Sidebar for Database Schema and API Key
with st.sidebar:
    st.title("🏦 Finance Database")
    
    provider = st.radio("Select AI Provider", ["Gemini", "Hugging Face"])
    
    if provider == "Gemini":
        api_key_input = st.text_input("Enter your Gemini API Key", type="password")
        if api_key_input:
            os.environ["GEMINI_API_KEY"] = api_key_input
            
        working_models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-pro"
        ]
    else:
        api_key_input = st.text_input("Enter your Hugging Face Token (Read)", type="password")
        if api_key_input:
            os.environ["HF_TOKEN"] = api_key_input
            os.environ["HUGGINGFACEHUB_API_TOKEN"] = api_key_input
            
        working_models = [
            "Qwen/Qwen2.5-7B-Instruct",
            "meta-llama/Meta-Llama-3-8B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "google/gemma-2-9b-it"
        ]
        
    st.divider()
    st.subheader("Model Selection")
    
    selected_model = st.selectbox("Select Model", working_models)
    
    # If the user selects a new provider or model, re-initialize the agent
    if "selected_provider" not in st.session_state or "selected_model" not in st.session_state or st.session_state.selected_provider != provider or st.session_state.selected_model != selected_model:
        st.session_state.selected_provider = provider
        st.session_state.selected_model = selected_model
        if "agent" in st.session_state:
            del st.session_state.agent
            
    st.divider()
    
    st.subheader("Database Context")
    if "agent" in st.session_state:
        st.code(st.session_state.agent.get_schema_string(), language='sql')
    else:
        st.write("Enter API Key/Token to load schema...")

# Main layout
st.title("🤖 Autonomous Natural Language-to-SQL Agent")

st.markdown("""
**An Agentic Project showcasing AI Tool-Calling, Schema Introspection, and ReAct Logic.**

This agent bridges the gap between natural language and a relational database. It runs on **LangChain** and dynamically reads the schema, writes SQL queries on the fly, executes them against the database, catches its own syntax errors to self-correct, and translates raw tabular data into conversational insights—all without any human intervention.
""")

with st.expander("System Architecture & Tech Stack"):
    st.markdown("""
    * **Orchestration**: LangChain (`create_sql_agent`)
    * **LLM Backends**: Gemini / Hugging Face Open-Source Models
    * **Agent Framework**: ReAct (Reason -> Act -> Observe) loop with recursive self-correction.
    * **Database**: Local SQLite 3 containing mock Financial structures (`clients`, `accounts`, `transactions`, `loans`).
    * **User Interface**: Streamlit with `StreamlitCallbackHandler` to visualize the agent's internal thought processes.
    """)
st.divider()

st.write("### Ask the Database a Question")
st.caption("Ask questions about clients, portfolios, transactions, and loans in plain English.")

# Check API key based on provider
if provider == "Gemini" and not os.environ.get("GEMINI_API_KEY"):
    st.warning("Please enter your Gemini API Key in the sidebar to start chatting.", icon="⚠️")
    st.stop()
elif provider == "Hugging Face" and not os.environ.get("HF_TOKEN"):
    st.warning("Please enter your Hugging Face API Token in the sidebar to start chatting.", icon="⚠️")
    st.stop()

# Initialize Agent
if "agent" not in st.session_state:
    try:
        with st.spinner("Connecting to Finance database and initializing Langchain..."):
            st.session_state.agent = SQLAgent(
                provider=st.session_state.get('selected_provider', 'Gemini'),
                model_name=st.session_state.get('selected_model', 'gemini-1.5-flash')
            )
        st.rerun() # Refresh so the sidebar gets the schema
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        st.stop()

# Initialize chat session
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hello! I am an Autonomous SQL Agent. I can query the database directly. What would you like to know?"}
    ]

# Display chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input(placeholder="e.g. Which clients have a balance over $100k?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        st_callback = StreamlitCallbackHandler(st.container())
        
        try:
            # Langchain invoke with the streamlit callback to visualize thoughts and SQL tool execution
            response = st.session_state.agent.agent_executor.invoke(
                {"input": prompt},
                {"callbacks": [st_callback]}
            )
            
            final_answer = response["output"]
            st.write(final_answer)
            st.session_state.messages.append({"role": "assistant", "content": final_answer})
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
