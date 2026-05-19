import os
from typing import TypedDict, Annotated, Sequence
import operator

from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint, HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

import db_setup

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_step: str
    sql_query: str
    sql_result: str
    rag_result: str

class SQLAgent:
    def __init__(self, provider: str = "Gemini", model_name: str = "gemini-1.5-flash"):
        # Ensure database is initialized
        db_setup.init_db()
        
        # Connect to the SQLite database
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_setup.DB_PATH}")
        
        if provider == "Gemini":
            self.api_key = os.environ.get("GEMINI_API_KEY")
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set.")
            
            # Initialize Gemini Model
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=0,
                google_api_key=self.api_key
            )
        elif provider == "Hugging Face":
            self.api_key = os.environ.get("HF_TOKEN")
            if not self.api_key:
                raise ValueError("HF_TOKEN environment variable not set.")
                
            # Initialize Hugging Face Endpoint
            base_llm = HuggingFaceEndpoint(
                repo_id=model_name,
                task="text-generation",
                max_new_tokens=512,
                huggingfacehub_api_token=self.api_key,
            )
            self.llm = ChatHuggingFace(llm=base_llm)
        else:
            raise ValueError(f"Unknown provider: {provider}")
            
        # Initialize RAG Retriever
        rag_embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        self.vector_store = Chroma(persist_directory="chroma_db", embedding_function=rag_embeddings)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        
        # --- Build the LangGraph Multi-Agent Workflow ---
        workflow = StateGraph(AgentState)
        
        # Add Nodes
        workflow.add_node("supervisor", self.node_supervisor)
        workflow.add_node("sql_expert", self.node_sql_expert)
        workflow.add_node("execute_sql", self.node_execute_sql)
        workflow.add_node("rag_expert", self.node_rag_expert)
        workflow.add_node("synthesizer", self.node_synthesizer)
        workflow.add_node("casual_chat", self.node_casual_chat)
        
        # Define Edges
        workflow.set_entry_point("supervisor")
        
        workflow.add_conditional_edges(
            "supervisor",
            lambda x: x["next_step"],
            {
                "sql_expert": "sql_expert",
                "rag_expert": "rag_expert",
                "casual_chat": "casual_chat"
            }
        )
        
        workflow.add_edge("sql_expert", "execute_sql")
        workflow.add_edge("execute_sql", "synthesizer")
        workflow.add_edge("rag_expert", "synthesizer")
        workflow.add_edge("synthesizer", END)
        workflow.add_edge("casual_chat", END)
        
        self.agent_executor = workflow.compile()

    def get_schema_string(self) -> str:
        """Returns the schema for display in UI"""
        return self.db.get_table_info()

    # --- Node Implementations ---
    
    def node_supervisor(self, state: AgentState):
        user_message = state["messages"][-1].content
        prompt = f"""You are the Supervisor of an AI Real Estate System.
Analyze this user query: '{user_message}'
Route it to the correct expert. Respond with ONLY ONE of the following words:
- sql_expert : If the user asks about specific properties, sales data, average prices, lot areas, or database queries.
- rag_expert : If the user asks about zoning rules, tax brackets, policies, or what zoning acronyms (like 'RL') mean.
- casual_chat : If the user says a simple greeting (like hi, hello) or asks something completely unrelated to real estate.
"""
        res = self.llm.invoke(prompt)
        decision = res.content.strip().lower()
        
        if "sql" in decision: next_step = "sql_expert"
        elif "rag" in decision or "zoning" in decision or "tax" in decision or "policy" in decision: next_step = "rag_expert"
        else: next_step = "casual_chat"
        
        return {"next_step": next_step}

    def node_sql_expert(self, state: AgentState):
        schema = self.get_schema_string()
        user_message = state["messages"][-1].content
        prompt = f"""You are a SQL Expert for the Ames Housing dataset.
Here is the SQLite schema:
{schema}

User Question: {user_message}

Write ONLY a valid SQL query to answer this question. Do NOT include markdown formatting like ```sql. Do not provide any explanation, just the raw SQL query.
"""
        res = self.llm.invoke(prompt)
        query = res.content.strip().replace("```sql", "").replace("```", "")
        return {"sql_query": query}
        
    def node_execute_sql(self, state: AgentState):
        query = state.get("sql_query", "")
        
        # HITL / Safety Guardrails
        destructive_keywords = ["drop", "delete", "update", "insert", "alter", "truncate"]
        if any(kw in query.lower() for kw in destructive_keywords):
            return {"sql_result": "SAFETY GUARDRAIL TRIGGERED: Query attempts to modify or delete data. Execution blocked.", "next_step": "end"}
            
        try:
            result = self.db.run(query)
            return {"sql_result": str(result)[:2000]} # Limit output length to prevent context overflow
        except Exception as e:
            return {"sql_result": f"SQL Error: {e}"}

    def node_rag_expert(self, state: AgentState):
        user_message = state["messages"][-1].content
        docs = self.retriever.invoke(user_message)
        context = "\n".join([doc.page_content for doc in docs])
        return {"rag_result": context}
        
    def node_synthesizer(self, state: AgentState):
        user_message = state["messages"][-1].content
        sql_res = state.get("sql_result", "None")
        rag_res = state.get("rag_result", "None")
        
        prompt = f"""You are a highly capable AI Real Estate Analyst.
Answer the user's question: '{user_message}'
Use the following retrieved data to formulate your answer:

--- SQL Query Results ---
{sql_res}

--- Knowledge Base (RAG) Results ---
{rag_res}

Provide a concise, helpful, and conversational response. If the data says an error occurred or the guardrail was triggered, politely inform the user.
"""
        res = self.llm.invoke(prompt)
        return {"messages": [AIMessage(content=res.content)]}
        
    def node_casual_chat(self, state: AgentState):
        return {"messages": [AIMessage(content="Hello! I am a Real Estate AI Agent powered by LangGraph. I can answer questions about the Ames housing market, calculate averages, and look up local zoning and tax laws. How can I help you today?")]}
