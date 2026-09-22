# Interview Script: Generalized Project Explanation

*Use this script when the interviewer asks: "Tell me about a recent project you built" or "Walk me through this AI agent project on your resume." This explanation removes the "Real Estate" specifics and focuses purely on the system design and architecture.*

---

## The Pitch (Elevator Pitch)

"I recently built a **Hybrid Autonomous Agentic System** using **LangGraph**. The goal of the project was to solve a common enterprise problem: business users need to extract insights from complex databases and company policy documents, but they don't know SQL or how to efficiently search through hundreds of unstructured PDFs. 

To solve this, I built an AI agent that takes natural language questions and autonomously routes them to either a structured data pipeline (SQL) or an unstructured data pipeline (RAG), executes the search locally, and synthesizes the answer."

## The Architecture (Walking them through the system)

"The core of the system is not just a simple API call; it's a multi-node state machine orchestrated by **LangGraph**. Let me walk you through the flow:

**1. The Router (Supervisor):** 
When a user asks a question, it hits my Supervisor node. I use a Large Language Model as a reasoning engine here. Its only job is intent classification—deciding if the user is asking for quantitative data (like sales figures or averages) or qualitative data (like rules or policies).

**2. The Structured Pipeline (SQL Expert):**
If the intent is quantitative, the graph routes to the SQL Expert node. 
*   **The trick here is data privacy.** I don't send the database to the LLM. I use schema introspection to extract just the table definitions and column names, and inject that into the prompt. 
*   The LLM generates a raw SQL query.
*   Then, it passes to my **Execution Node**. I built a safety guardrail here that scans the SQL for destructive commands like `DROP` or `DELETE` to prevent SQL injection or hallucination-based data loss. If it passes, it executes the query locally against a SQLite database.

**3. The Unstructured Pipeline (RAG Expert):**
If the intent is qualitative, the graph routes to my RAG (Retrieval-Augmented Generation) node. 
*   I built a vector database using **ChromaDB**. 
*   I used local **HuggingFace embeddings** (`all-MiniLM-L6-v2`) to chunk and embed documents. 
*   The system performs a local similarity search to pull the top 3 most relevant context chunks.

**4. The Synthesizer:**
Finally, whether the data came from the SQL database or the Vector database, the raw results flow into a Synthesizer node. The LLM takes this raw context and formulates a clean, human-readable response back to the user via a Streamlit frontend."

## The Impact / Why it matters

"What I'm most proud of with this architecture is that it eliminates the 'Black Box' problem. Because it's built on LangGraph, I can trace exactly which nodes fired, what the generated SQL was, and what context was retrieved. Furthermore, by executing the SQL and RAG locally, I ensured that proprietary data never leaves the server, and the LLM is only used strictly for reasoning and translation, not data storage."

---

### Tips for Delivery:
*   **Pause after explaining the Router.** Make sure they understand it's a multi-path system.
*   **Emphasize "Local Execution" and "Schema Introspection".** Interviewers love hearing about data privacy and context window optimization.
*   **Emphasize the "Guardrails".** Showing that you thought about an LLM maliciously or accidentally deleting a database (`DROP TABLE`) proves you think like a production-level engineer.
