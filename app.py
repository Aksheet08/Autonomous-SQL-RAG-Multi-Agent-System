import os
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

import streamlit as st

try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_core.messages import HumanMessage, AIMessage
from agent import SQLAgent

st.set_page_config(page_title="Real Estate AI Agent", page_icon="🏡", layout="wide")

# Sidebar for Database Schema and API Key
with st.sidebar:
    st.title("🏡 Real Estate Database")
    
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
st.title("🏡 Autonomous Real Estate AI Agent")

st.markdown("""
**A Hybrid Agentic System powered by LangGraph, Schema Introspection, and RAG.**

This AI bridges the gap between natural language, the massive **Ames Housing database**, and **local municipal zoning and tax laws**. Ask it a complex property or legal question, and watch the Supervisor node autonomously route the task to the SQL Expert or the RAG Expert in real-time!
""")

with st.expander("System Architecture & Tech Stack"):
    st.markdown("""
    * **Orchestration**: LangGraph (`StateGraph`, `Nodes`, `Edges`)
    * **LLM Backends**: Gemini / Hugging Face Open-Source Models
    * **Agent Framework**: Multi-Agent Routing System (Supervisor -> SQL Expert / RAG Expert) with HITL Guardrails.
    * **Database**: Local SQLite 3 containing the real Ames Housing dataset (2930 properties, 82 columns).
    * **Vector Store**: ChromaDB with `all-MiniLM-L6-v2` embeddings for Ames Zoning and Tax Laws.
    * **User Interface**: Streamlit with LangGraph Event Streaming.
    """)
    
    st.write("### 🏗️ Flowchart")
    
    # Render Mermaid using Streamlit HTML component
    mermaid_code = """
    graph TD
        User(["👤 User"]) --> UI["💻 Streamlit UI"]
        UI --> Supervisor{"🕵️ Supervisor Router"}
        
        Supervisor -->|Database Queries| SQLExpert["📊 SQL Expert"]
        Supervisor -->|Policy/Zoning Queries| RAGExpert["📚 RAG Expert"]
        Supervisor -->|Greetings/Other| CasualChat["💬 Casual Chat"]
        
        SQLExpert -->|Generates SQL| Guardrails{"🛡️ Safety Guardrails"}
        Guardrails -->|Blocks Destructive SQL| Error["⚠️ Return Error"]
        Guardrails -->|Executes Safe SQL| DB[("🗄️ SQLite Database")]
        
        RAGExpert -->|Embeds & Searches| VectorDB[("🧠 Chroma Vector Store")]
        
        DB --> Synthesizer["✍️ Synthesizer"]
        VectorDB --> Synthesizer
        Error --> Synthesizer
        
        Synthesizer --> UI
        CasualChat --> UI
    """
    
    import streamlit.components.v1 as components
    components.html(
        f"""
        <div class="mermaid">
            {mermaid_code}
        </div>
    
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{ startOnLoad: true }});
        </script>
        """,
        height=600,
        scrolling=True
    )

st.divider()

st.write("### Ask the Database a Question")
st.caption("Ask questions about property sales, lot areas, tax rates, and zoning codes in plain English.")

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
        with st.spinner("Connecting to Real Estate database and compiling LangGraph..."):
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
        {"role": "assistant", "content": "Hello! I am a Hybrid Real Estate AI Agent. I can query the property database and look up Ames zoning rules. What would you like to know?"}
    ]

# Display chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input(placeholder="e.g. What is the average lot area for RL zoned homes?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        try:
            with st.status("Agent Thinking...", expanded=True) as status:
                final_answer = ""
                
                # Stream events from LangGraph
                for event in st.session_state.agent.agent_executor.stream({"messages": [HumanMessage(content=prompt)]}):
                    for node_name, node_state in event.items():
                        st.write(f"🟢 **Node executed:** `{node_name}`")
                        
                        if node_name == "sql_expert" and "sql_query" in node_state:
                            st.code(node_state["sql_query"], language="sql")
                        elif node_name == "execute_sql" and "sql_result" in node_state:
                            st.markdown("**Database Result:**")
                            st.code(node_state["sql_result"])
                        elif node_name == "rag_expert":
                            st.info("🔍 Scanned Knowledge Base for Policies.")
                            
                        # Check if this node added messages to the state
                        if "messages" in node_state and len(node_state["messages"]) > 0:
                            last_msg = node_state["messages"][-1]
                            if isinstance(last_msg, AIMessage):
                                final_answer = last_msg.content
                
                status.update(label="Complete", state="complete", expanded=False)
                
            if not final_answer:
                final_answer = "I'm sorry, I couldn't process that request."
                
            st.write(final_answer)
            st.session_state.messages.append({"role": "assistant", "content": final_answer})
            
        except Exception as e:
            st.error(f"An error occurred: {e}")
