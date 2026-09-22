import os
from dotenv import load_dotenv

load_dotenv()
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

# Ensure LANGCHAIN_TRACING_V2 is active if LANGCHAIN_API_KEY is present
if os.environ.get("LANGCHAIN_API_KEY"):
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.setdefault("LANGCHAIN_PROJECT", "real-estate-agent-eval")

import pandas as pd
from datasets import Dataset
from agent import SQLAgent
from langchain_core.messages import HumanMessage, AIMessage

from ragas import evaluate
from ragas.metrics.collections import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings

def run_evaluation():
    # 1. Prepare evaluation dataset
    eval_questions = [
        "What is the average lot area for RL zoned homes?"
    ]
    
    # Ground truth answers
    ground_truths = [
        "The average lot area for RL zoned homes is around 10000 to 11000 square feet."
    ]
    
    print("Initializing agent...")
    agent = SQLAgent(model_name="gemini-2.5-flash")
    
    answers = []
    contexts_list = []
    
    print("Generating responses...")
    for q in eval_questions:
        print(f"Question: {q}")
        final_answer = ""
        retrieved_context = ""
        
        # We need to preserve the state between loops, but since it's an evaluation, we can do 1 query per run
        # LangGraph state needs to be freshly initiated for each question
        for event in agent.agent_executor.stream({"messages": [HumanMessage(content=q)], "next_step": "", "sql_query": "", "sql_result": "", "rag_result": ""}):
            for node_name, node_state in event.items():
                if node_name == "rag_expert" and "rag_result" in node_state:
                    retrieved_context = node_state["rag_result"]
                    
                if "messages" in node_state and len(node_state["messages"]) > 0:
                    last_msg = node_state["messages"][-1]
                    if isinstance(last_msg, AIMessage):
                        final_answer = last_msg.content
                        
        answers.append(final_answer)
        contexts_list.append([retrieved_context] if retrieved_context else ["No context retrieved."])
        
        print("Waiting 15 seconds to respect Gemini Free Tier rate limits...")
        import time
        time.sleep(15)
        
    data = {
        "question": eval_questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths
    }
    
    dataset = Dataset.from_dict(data)
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found. Please set it in .env file.")
        return
        
    print("Initializing Ragas Evaluator Models...")
    evaluator_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=api_key
    )
    evaluator_embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    ragas_llm = LangchainLLMWrapper(evaluator_llm)
    ragas_embeddings = LangchainEmbeddingsWrapper(evaluator_embeddings)
    
    print("Waiting 60 seconds for Gemini API rate limits to reset before starting Ragas evaluation...")
    import time
    time.sleep(60)
    from ragas.run_config import RunConfig

    print("Running evaluation...")
    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision,
        ],
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        run_config=RunConfig(max_workers=1)
    )
    
    print("\n=== Evaluation Results ===")
    print(result)
    
    df = result.to_pandas()
    df.to_csv("evaluation_results.csv", index=False)
    print("Detailed results saved to evaluation_results.csv")

if __name__ == "__main__":
    run_evaluation()
