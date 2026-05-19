import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

DOCS_DIR = "documents"
CHROMA_PATH = "chroma_db"

def init_rag():
    print("Initializing RAG vector store...")
    
    # 1. Load Documents
    if not os.path.exists(DOCS_DIR):
        print(f"Directory {DOCS_DIR} not found. Please create it and add text documents.")
        return
        
    loader = DirectoryLoader(DOCS_DIR, glob="**/*.txt", loader_cls=TextLoader)
    documents = loader.load()
    
    if not documents:
        print(f"No text documents found in {DOCS_DIR}.")
        return
        
    print(f"Loaded {len(documents)} documents.")

    # 2. Split Text
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split documents into {len(chunks)} chunks.")

    # 3. Create Embeddings & Store in Chroma
    # We use a small, efficient local model for embeddings so it doesn't require an API key
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Clear out the existing database directory if you want to rebuild from scratch
    # (Chroma manages its own files, but this ensures a clean slate)
    if os.path.exists(CHROMA_PATH):
        import shutil
        shutil.rmtree(CHROMA_PATH)
        
    # Create the vector store
    db = Chroma.from_documents(
        chunks, embeddings, persist_directory=CHROMA_PATH
    )
    
    print(f"Saved vector database to {CHROMA_PATH}.")

if __name__ == "__main__":
    init_rag()
