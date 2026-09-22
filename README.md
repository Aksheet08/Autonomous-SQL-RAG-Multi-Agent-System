# 🏡 Autonomous Hybrid Real Estate AI Agent

An enterprise-grade **Multi-Agent System** that bridges the gap between natural language, messy real-world databases, and unstructured policy documents. 

This agent dynamically reads an 82-column database schema(Ames Housing Dataset), writes complex SQL queries on the fly, searches through internal municipal zoning and tax documents, and synthesizes answers using a **LangGraph State Machine**—all protected by strict human-in-the-loop (HITL) execution guardrails.

## 📖 About the Project

Real estate agents, investors, and city planners often have to navigate disjointed systems: massive SQL databases containing numerical property data, and giant PDF documents containing dense municipal zoning laws. 

This project solves that by creating a single conversational interface. You can ask it natural language questions like *"What is the average price of a home in a Low Density Residential zone?"* 
The AI will autonomously realize it needs to search the knowledge base to figure out what "Low Density Residential" means (`RL`), and then write and execute the exact SQL query required to calculate the average price from the database—and return a synthesized answer!

## 🏗️ System Architecture
```mermaid
flowchart TD
    User([👤 User]) --> UI[💻 Streamlit UI]
    UI --> Supervisor{🕵️ Supervisor Router}
    
    Supervisor -->|Database Queries| SQLExpert[📊 SQL Expert]
    Supervisor -->|Policy/Zoning Queries| RAGExpert[📚 RAG Expert]
    Supervisor -->|Greetings/Other| CasualChat[💬 Casual Chat]
    
    SQLExpert -->|Generates SQL| Guardrails{🛡️ Safety Guardrails}
    Guardrails -->|Blocks Destructive SQL| Error[⚠️ Return Error]
    Guardrails -->|Executes Safe SQL| DB[(🗄️ SQLite Database)]
    
    RAGExpert -->|Embeds and Searches| VectorDB[(🧠 Chroma Vector Store)]
    
    DB --> Synthesizer[✍️ Synthesizer]
    VectorDB --> Synthesizer
    Error --> Synthesizer
    
    Synthesizer --> UI
    CasualChat --> UI
```

## 🌐 Live Demo

🚀 Experience an Interactive Live Chatbot:  
👉 [Open Live App](https://autonomous-sql-agent-6fjky6ynvy9zs8smcy8ahm.streamlit.app/)

## 🌟 Key Features
* **Multi-Agent Architecture (LangGraph):** Upgraded from a simple LangChain ReAct loop to a scalable LangGraph architecture featuring a Supervisor Router, a SQL Expert, and a RAG Expert.
* **Retrieval-Augmented Generation (RAG):** Uses a local ChromaDB vector store to embed local Ames zoning laws and tax rules, acting as a dynamic "Data Dictionary" for cryptic database columns (e.g. knowing that "Residential Low Density" maps to `MS_Zoning = 'RL'`).
* **Real-World Dataset:** Automatically provisions an embedded SQLite database containing the massive **Ames Housing Dataset** (2,930 rows, 82 columns) to demonstrate true schema introspection capabilities.
* **Safety Execution Guardrails:** The SQL Engine intercepts and scans all LLM-generated queries for destructive actions (`DROP`, `DELETE`, `UPDATE`, `INSERT`). Malicious queries are instantly blocked before hitting the database.
* **Thought Visualization UI:** Built on Streamlit, allowing users to watch the LangGraph event stream in real-time to see exactly which sub-agents are being activated.
* **Full-Stack Observability:** Integrated with **LangSmith** to provide detailed telemetry, execution traces, and token usage statistics for every LangGraph node execution.
* **Automated Offline Evaluation:** Includes a **Ragas** LLM-as-a-judge evaluation suite (`evaluate.py`) that mathematically scores the agent's RAG pipeline across Faithfulness, Answer Relevancy, Context Recall, and Context Precision.

## 🛠️ Technology Stack
* **Language:** Python
* **Orchestration:** LangGraph (`StateGraph`, `Nodes`, `Edges`)
* **Vector Store / RAG:** ChromaDB, `sentence-transformers` (`all-MiniLM-L6-v2`)
* **LLM Engine:** Google Gemini (Gemini 2.5 Flash / Pro)
* **Observability & Evaluation:** LangSmith, Ragas
* **Frontend:** Streamlit
* **Database:** SQLite3, Pandas

## 📊 About the Ames Housing Dataset
This project utilizes the **Ames Housing Dataset** (compiled by Dean De Cock), a widely respected benchmark containing real-world data on **2,930 individual residential property sales** in Ames, Iowa, from 2006 to 2010. 
* **High-Dimensional Complexity:** Features 82 distinct columns detailing property size, quality, building materials, zoning codes, and sales details.
* **Cryptic Encoding:** Many columns use encoded acronyms (e.g., `MS_Zoning = 'RL'` for Residential Low Density). This agent leverages RAG as a semantic dictionary to decode queries before executing them.
* **Official Documentation:** Check out the official [Ames Housing Codebook](https://jse.amstat.org/v19n3/decock/DataDocumentation.txt) for detailed column definitions.


## 🚀 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/nl-to-sql-agent.git
   cd nl-to-sql-agent
   ```

2. **Set up a Virtual Environment:**
   Run the following commands to create and activate an isolated environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the Database and Knowledge Base:**
   Download the real-world dataset and embed the zoning documents:
   ```bash
   python db_setup.py
   python rag_setup.py
   ```

5. **Run the Application:**
   Start the Streamlit development server:
   ```bash
   streamlit run app.py
   ```

## 🔐 Configuration
To enable the application and LangSmith tracing, create a `.env` file in the root directory and add your API keys:

```env
LANGCHAIN_API_KEY=lsv2_pt_your_langsmith_key
GEMINI_API_KEY=your_gemini_api_key
```
*(Note: You can also enter the Gemini API Key directly into the Streamlit sidebar if you prefer not to use the `.env` file, but the `.env` file is required for `evaluate.py` to run).*

## 📈 Running the Evaluation Suite
You can test the statistical accuracy of the agent using the Ragas offline evaluation script:
```bash
python evaluate.py
```
This will run the agent through a test set and save the results (Faithfulness, Relevancy, etc.) to `evaluation_results.csv`.

## 💡 Example Queries
* **Database Query:** "What is the average Sale_Price of homes that have an 'Excellent' Basement_Qual?"
* **Policy Query (RAG):** "If I buy a property in an RM zone, can I build an Accessory Dwelling Unit?"
* **Hybrid Query:** "What is the average Lot_Area for homes in a Residential Low Density zone?" *(The agent will use RAG to map 'Low Density' to 'RL', and then write the SQL!)*
* **Guardrail Test:** "Drop the properties table." *(Watch the execution engine block the request).*

---
*Built as a showcase for Advanced Agentic Data Engineering workflows.*
