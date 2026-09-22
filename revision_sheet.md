# 🚀 Last-Minute Revision Sheet

*Scan this 15 minutes before your interview to keep the technical details fresh.*

## 🛠 Tech Stack Overview
*   **Orchestration Framework:** LangGraph (StateGraph) & LangChain
*   **UI/Frontend:** Streamlit (`app.py`)
*   **Relational DB:** SQLite (`db_setup.py`)
*   **Vector DB:** ChromaDB (`rag_setup.py`)
*   **Embeddings:** HuggingFace `all-MiniLM-L6-v2` (runs locally, no API cost)
*   **LLMs Supported:** Google Gemini (`gemini-1.5-flash`), HuggingFace Endpoint (Qwen, Llama3)
*   **Data Processing:** Pandas (for initial CSV load to SQLite)

## 🧠 LangGraph Node Flow
1.  **`supervisor`:** The brain/router. Decides: SQL, RAG, or Casual Chat.
2.  **`sql_expert`:** Generates SQL using DB Schema.
3.  **`execute_sql`:** Runs SQL against SQLite. **Contains Safety Guardrails.**
4.  **`rag_expert`:** Retrieves top-k chunks from ChromaDB.
5.  **`synthesizer`:** Combines raw results (SQL/RAG) into a human answer.
6.  **`casual_chat`:** Fallback for greetings.

## 🛡 How to Defend Your Architecture

**1. Is it a Black Box?**
*   **NO.** It uses LangGraph's deterministic routing. We can stream the execution state and see exactly what the LLM generated at every node. It's a traceable graph, not a single opaque prompt.

**2. Are you leaking database data to OpenAI/Google?**
*   **NO.** Only the **Schema** (Table names, Column names) is sent to the LLM to generate the query. The actual SQL execution happens **locally** via `sqlite3`. The database rows never go to the LLM API until the final synthesis phase, and even then, results are truncated.

**3. What if the LLM hallucinates a `DROP TABLE` command?**
*   **Handled.** The `execute_sql` node intercepts the query before execution. If it contains `['drop', 'delete', 'update', 'insert', 'alter', 'truncate']`, it is immediately blocked and returns a safety warning.

**4. Why LangGraph over standard LangChain Agents (ReAct)?**
*   Standard agents loop unpredictably. LangGraph allows for defined, cyclical or acyclic **State Machines**. It gives granular engineering control over the exact flow and allows injecting manual code (like guardrails) between LLM thoughts.

**5. How does the Vector Database work?**
*   `RecursiveCharacterTextSplitter` chunks documents -> `HuggingFaceEmbeddings` converts text to vectors (arrays of floats) -> `ChromaDB` stores them. When queried, it uses **Cosine Similarity** to find the closest matching text chunks.

## 🔑 Buzzwords to use in the interview
*   **Agentic Workflow**
*   **Routing Architecture**
*   **Schema Introspection**
*   **Retrieval-Augmented Generation (RAG)**
*   **Semantic Similarity Search**
*   **Safety Guardrails / Human-in-the-Loop (HITL) concepts**
*   **Deterministic State Machine**
