# 🤖 Autonomous Natural Language-to-SQL Agent

An end-to-end Data Engineering & Generative AI project that bridges the gap between natural language (plain English) and structured SQL databases. This agent dynamically reads database schemas, writes SQL queries on the fly, executes them against an in-memory database, catches its own syntax errors to self-correct, and translates raw tabular data back into conversational insights—all without any human intervention.

## 🌟 Key Features
* **ReAct Agent Architecture:** Utilizes LangChain's SQL Toolkits to create a Reason-Act-Observe loop that allows the LLM to recursively inspect database schemas and debug its own queries.
* **Dual AI Providers:** Dynamically switch between **Google Gemini** APIs and **Hugging Face Serverless Inference API** (bringing support to completely open-source, ungated models like `Qwen/Qwen2.5-7B-Instruct`).
* **Financial Mock Database:** Automatically provisions an embedded SQLite database containing realistic structural mock data for `clients`, `accounts`, `transactions`, and `loans`.
* **Thought Visualization UI:** Built on Streamlit using Langchain's native `StreamlitCallbackHandler`, allowing users to literally "see" the intermediate SQL queries and raw data returns the model is reviewing in real-time.

## 🛠️ Technology Stack
* **Language:** Python
* **Orchestration:** LangChain (`create_sql_agent`, `SQLDatabase`)
* **LLM Engine:** Gemini 1.5/2.5 or Hugging Face Inference Hub
* **Frontend:** Streamlit
* **Database:** SQLite3

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

4. **Run the Application:**
   Start the Streamlit development server:
   ```bash
   streamlit run app.py
   ```

## 🔐 Configuration
You do *not* need to hard-code your environment variables. The Streamlit UI is built with secure password-masked sidebars where you can input:
* Your **Gemini API Key** (Generated via Google AI Studio)
* Your **Hugging Face Token** (Requires Read/Inference access if using gated models like Llama-3)

## 💡 Example Queries
* "Which clients have a total balance across all their accounts over $100k?"
* "What is the principal remaining on loans for clients who joined in 2021?"
* "Show me all transactions that occurred at a Grocery Store, mapped to the client's first name."

---
*Built as a showcase for Agentic Data Engineering workflows.*
