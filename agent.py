import os
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
import db_setup

class SQLAgent:
    def __init__(self, provider: str = "Gemini", model_name: str = "gemini-1.5-flash"):
        # Ensure database is initialized
        db_setup.init_db()
        
        # Connect to the SQLite database using LangChain's SQLDatabase utility
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
            
        if provider == "Gemini":
            agent_type = "tool-calling"
        else:
            # Open source models on HF inference API usually don't support strict JSON tool-calling
            agent_type = "zero-shot-react-description"
            
        custom_prefix = """You are an AI Financial Data Analyst. 
If the user's input is a simple greeting (e.g., 'hi', 'hello', 'how are you') or unrelated to the database, DO NOT use any database tools. Instead, simply respond conversationally and ask how you can help them with their financial data.
Only use the database tools if the user asks a specific question about clients, accounts, transactions, or loans.
"""

        # Create standard Langchain SQL Agent
        self.agent_executor = create_sql_agent(
            llm=self.llm,
            db=self.db,
            agent_type=agent_type,
            verbose=True,
            handle_parsing_errors=True,
            prefix=custom_prefix
        )

    def ask(self, user_question: str) -> dict:
        """
        Runs the agent and returns the final response and intermediate steps.
        """
        # Hard-coded safety net for standard greetings to save tokens and prevent tool loops
        clean_q = user_question.lower().strip().replace("?", "").replace("!", "")
        greetings = ["hi", "hello", "hey", "how are you", "who are you", "what's up", "good morning"]
        
        if clean_q in greetings or (len(clean_q.split()) <= 2 and clean_q.startswith(("hi", "hello", "hey"))):
            return {"output": "Hello! I am your AI Financial Analyst. I can pull real-time data about clients, accounts, transactions, and loans. How can I help you query the database today?"}
            
        # The Streamlit callback will handle the rendering of intermediate steps
        return self.agent_executor.invoke({"input": user_question})

    def get_schema_string(self) -> str:
        """Returns the schema for display in UI"""
        return self.db.get_table_info()
