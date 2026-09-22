# Comprehensive Project Guide: NL to SQL & RAG Hybrid Agent (With Code & Tech Walkthroughs)

This document breaks down your project in extreme detail. It is designed to prepare you for technical interviews by explaining the architecture, the code, the data flow, the core technologies, and demystifying the "black box" aspect of AI.

## 1. Project Overview

**What is it?**
It is a hybrid AI agentic system powered by LangGraph. It bridges the gap between natural language and complex data. It can answer questions from both **structured data** (a SQL database) and **unstructured data** (text documents like policies and rules).

**Tech Stack:**
*   **Orchestration:** LangGraph & LangChain
*   **Frontend:** Streamlit
*   **Structured Database:** SQLite & Pandas (for data ingestion)
*   **Vector Database (RAG):** ChromaDB & HuggingFace Embeddings (`all-MiniLM-L6-v2`)
*   **LLM Providers:** Google Gemini & Hugging Face

---

## 2. Core Concepts & Technologies Explained

Interviewers will test your fundamental understanding of the tools you used. Here is how you explain them:

### What is LangChain?
**LangChain** is the standard framework for building applications powered by LLMs. You use it as the "plumbing" of your application. Instead of writing raw HTTP requests to OpenAI or Google, LangChain provides standardized, modular components for Document Loading (`DirectoryLoader`), Text Splitting, and LLM interfaces.

### What is LangGraph (and why not just use LangChain Agents)?
**LangGraph** is an extension of LangChain used to build stateful, multi-actor agents. 
*   *The Problem it Solves:* Standard LangChain Agents (like ReAct agents) operate in a "while loop" where the LLM continuously decides what tool to use until it's done. This is unpredictable and can lead to infinite loops.
*   *The LangGraph Solution:* LangGraph treats the application as a **Directed Graph (State Machine)**. You define specific nodes (functions) and edges (conditional routing). It maintains a central `State` object that gets passed around. This gives you deterministic, granular engineering control over the execution flow, which is mandatory for production safety.

### What is RAG (Retrieval-Augmented Generation)?
**RAG** is a technique to stop LLMs from hallucinating by grounding them in your private data. LLMs only know what they were trained on. If you ask an LLM about your company's private zoning policy, it will guess. With RAG, you:
1.  **Retrieve** relevant documents based on the user's question.
2.  **Augment** the LLM prompt by pasting that document text inside it.
3.  **Generate** the final answer.

### What are Embeddings and Vector Databases?
To make RAG work, you need to search text by its *meaning*, not just exact keyword matches.
*   **Embeddings:** You pass a chunk of text into an Embedding Model (like HuggingFace `all-MiniLM-L6-v2`). The model converts the text into a dense vector (an array of hundreds of floating-point numbers). Concepts that are semantically similar (e.g., "dog" and "puppy") will have vectors that are mathematically close to each other in high-dimensional space.
*   **Vector Database (ChromaDB):** Standard databases (like SQL) are bad at comparing arrays of numbers. A Vector Database is highly optimized to store these embeddings and perform extremely fast mathematical comparisons (usually **Cosine Similarity**) to find the text chunks that most closely match the user's question.

---

## 3. Architecture & Data Flow: Defeating the "Black Box"

**"No, it is not a black box. The system operates on a locally defined graph architecture with strict routing and safety guardrails."**

### Where is the data going? (The Flow)
1.  **User Input:** The user types a question in the Streamlit frontend.
2.  **Supervisor Node (LLM API Call 1):** The question is sent to the LLM with a specific system prompt acting as a router. **No database data is sent here.** The LLM only sees the question and decides if it needs the `SQL_Expert` or `RAG_Expert`.
3.  **Expert Node:**
    *   **If SQL:** The agent sends the *Database Schema* (column names, table names) and the user's question to the LLM (API Call 2). **No actual row data is sent to the LLM API.**
    *   **If RAG:** The agent runs a local similarity search in ChromaDB using HuggingFace embeddings. It retrieves relevant text chunks locally.
4.  **Execution (Local):** The generated SQL query is executed *locally* on your SQLite database. The data never leaves your server during execution.
5.  **Synthesizer (LLM API Call 3):** The local SQL results (or RAG context) are combined with the user's question and sent to the LLM to formulate a human-readable, conversational answer.

---

## 4. Major Code Explanations

Here we break down the most critical parts of the codebase.

### A. Database Setup (`db_setup.py`)

```python
def init_db():
    # Load data using Pandas directly from a URL
    df = pd.read_csv(CSV_URL)
    
    # Clean column names (replace spaces with underscores to prevent SQL syntax errors)
    df.columns = df.columns.str.replace(' ', '_').str.replace('/', '_').str.replace('-', '_')
    
    # Connect to local SQLite database (creates real_estate.db file)
    conn = sqlite3.connect(DB_PATH)
    
    # Write the Pandas DataFrame into a SQLite table named 'properties'
    df.to_sql('properties', conn, if_exists='replace', index=False)
```
**Explanation for Interview:** "I used Pandas to initially ingest and clean the CSV data, specifically removing spaces in column headers so they act as valid SQL identifiers. Then, I leveraged Pandas' built-in `to_sql` method to instantly spin up a local SQLite database file. This ensures the data is stored locally and securely, ready to be queried by the agent offline."

### B. RAG Setup (`rag_setup.py`)

```python
def init_rag():
    # 1. Load Documents using LangChain's DirectoryLoader
    loader = DirectoryLoader(DOCS_DIR, glob="**/*.txt", loader_cls=TextLoader)
    documents = loader.load()

    # 2. Split Text into smaller chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50, # Overlap prevents cutting off context mid-sentence
        length_function=len,
    )
    chunks = text_splitter.split_documents(documents)

    # 3. Create Embeddings & Store in Chroma (Local execution)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma.from_documents(chunks, embeddings, persist_directory=CHROMA_PATH)
```
**Explanation for Interview:** "For unstructured data, I built a standard RAG pipeline. I used `RecursiveCharacterTextSplitter` to break large policy text files into chunks of 500 characters with a 50-character overlap. Crucially, I used a small, open-source HuggingFace model (`all-MiniLM-L6-v2`) for the embeddings. This means the vectorization happens locally on the CPU, and no API keys or cloud costs are incurred for embedding. The vectors are then persisted locally using ChromaDB."

### C. The Core Brain: LangGraph (`agent.py`)

#### 1. Defining the State
```python
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_step: str
    sql_query: str
    sql_result: str
    rag_result: str
```
**Explanation:** "LangGraph relies on a state object that gets passed from node to node. I defined `AgentState` as a TypedDict. It stores the chat history (`messages`), the router's decision (`next_step`), and the intermediate variables like the raw SQL query, the SQL output, and the RAG context. This allows every node to append data to the central memory."

#### 2. The Supervisor (Router) Node
```python
    def node_supervisor(self, state: AgentState):
        user_message = state["messages"][-1].content
        prompt = f"""You are the Supervisor...
Route it to the correct expert. Respond with ONLY ONE of the following words:
- sql_expert : If user asks about specific properties, sales data, average prices...
- rag_expert : If user asks about zoning rules, tax brackets, policies...
"""
        res = self.llm.invoke(prompt)
        decision = res.content.strip().lower()
        
        # Set the next_step in the state based on LLM's decision
        if "sql" in decision: next_step = "sql_expert"
        elif "rag" in decision: next_step = "rag_expert"
        else: next_step = "casual_chat"
        
        return {"next_step": next_step}
```
**Explanation:** "The Supervisor node acts as a zero-shot classifier. It takes the latest user message and prompts the LLM to choose an expert. By strictly constraining its output to predefined keywords, I can confidently map its response to an execution path in the graph."

#### 3. The SQL Execution (Guardrails)
```python
    def node_execute_sql(self, state: AgentState):
        query = state.get("sql_query", "")
        
        # HITL / Safety Guardrails (Crucial for interviews)
        destructive_keywords = ["drop", "delete", "update", "insert", "alter", "truncate"]
        if any(kw in query.lower() for kw in destructive_keywords):
            return {"sql_result": "SAFETY GUARDRAIL TRIGGERED: Execution blocked."}
            
        try:
            result = self.db.run(query) # Local SQLite execution
            return {"sql_result": str(result)[:2000]} # Truncate to prevent context overflow
        except Exception as e:
            return {"sql_result": f"SQL Error: {e}"}
```
**Explanation:** "This node is proof that the system is not a black box. Before running any LLM-generated code against the database, I intercept it. I check for destructive SQL keywords. If the LLM hallucinates a `DROP TABLE` command, it is caught here and blocked. If it's safe, it executes locally. Additionally, I truncate the output to 2000 characters to ensure we don't blow up the LLM's context window limit in the next step."

#### 4. Compiling the Graph
```python
        workflow = StateGraph(AgentState)
        
        # Add Nodes to the graph
        workflow.add_node("supervisor", self.node_supervisor)
        workflow.add_node("sql_expert", self.node_sql_expert)
        workflow.add_node("execute_sql", self.node_execute_sql)
        
        # Define Edges (The Flow)
        workflow.set_entry_point("supervisor")
        workflow.add_conditional_edges("supervisor", lambda x: x["next_step"], {
                "sql_expert": "sql_expert",
                "rag_expert": "rag_expert",
                "casual_chat": "casual_chat"
        })
        workflow.add_edge("sql_expert", "execute_sql")
        workflow.add_edge("execute_sql", "synthesizer")
        
        self.agent_executor = workflow.compile()
```
**Explanation:** "I used LangGraph to compile the state machine. The `add_conditional_edges` function evaluates the `next_step` variable set by the Supervisor, branching the logic. This deterministic graph structure is far superior and more reliable than standard agent loops (like ReAct), because I explicitly control the flow."

---

## 5. Anticipated Interview Questions & Answers

> [!CAUTION]
> **Q: "Isn't this just a wrapper around ChatGPT/Gemini? What did you actually build?"**
> **A:** "No, the LLM is just the reasoning engine. I built the orchestration layer. The LLM cannot query a database on its own. I built a LangGraph state machine that routes logic, intercepts LLM hallucinations, enforces database schema injection, executes queries locally in a sandboxed SQLite environment, and combines it with local ChromaDB embeddings. I built the guardrails and the architecture, not just a prompt."

> [!WARNING]
> **Q: "What happens if the LLM generates a query like `DROP TABLE properties;`?"**
> **A:** "I implemented a safety guardrail in the `execute_sql` node. Before any SQL query hits the database, I parse it for destructive keywords (drop, delete, update, truncate). If detected, execution is immediately blocked and a safety warning is returned to the user."

> [!NOTE]
> **Q: "How did you handle the context window limits? Databases are huge."**
> **A:** "I don't send the database rows to the LLM. I use Schema Introspection. Only the `get_table_info()` (the column names and types) is sent in the prompt. When the SQL query executes locally, I also truncate the result to 2000 characters before sending it back to the Synthesizer node to prevent context overflow."
