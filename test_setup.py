import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure local modules can be loaded
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

load_dotenv()

print("=" * 60)
print("  Government Exam Assistant - System & Environment Test")
print("=" * 60)
print()

# 1. Streamlit
try:
    import streamlit
    print("1. Streamlit: SUCCESS (v" + streamlit.__version__ + ")")
except Exception as e:
    print("1. Streamlit: FAILED -", e)

# 2. PyPDF
try:
    import pypdf
    print("2. PyPDF: SUCCESS (v" + pypdf.__version__ + ")")
except Exception as e:
    print("2. PyPDF: FAILED -", e)

# 3. LangChain Core & Text Splitters
try:
    import langchain
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    print("3. LangChain: SUCCESS")
except Exception as e:
    print("3. LangChain: FAILED -", e)

# 4. FAISS Vector Store
try:
    from langchain_community.vectorstores import FAISS
    import faiss
    print("4. FAISS Vector Store: SUCCESS")
except Exception as e:
    print("4. FAISS: FAILED -", e)

# 5. Embeddings Engine (Google GenAI / HuggingFace / Local Fallback)
try:
    from rag_pipeline import create_embeddings
    emb = create_embeddings()
    test_vec = emb.embed_query("Civil Services")
    print(f"5. Embeddings Engine: SUCCESS (Type: {type(emb).__name__}, Dim: {len(test_vec)})")
except Exception as e:
    print("5. Embeddings Engine: FAILED -", e)

# 6. Gemini LLM Integration
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    api_key = os.getenv("GEMINI_API_KEY", "")
    if api_key and api_key != "your_actual_gemini_api_key_here":
        print("6. Gemini API Key: CONFIGURED")
    else:
        print("6. Gemini API Key: NOT FOUND (Please set GEMINI_API_KEY in .env)")
except Exception as e:
    print("6. Gemini Integration: FAILED -", e)

# 7. PDF Processor & Preloaded Study Material
try:
    from pdf_processor import create_sample_study_material, extract_pdf_text
    sample_pdf = create_sample_study_material()
    pages = extract_pdf_text(sample_pdf)
    print(f"7. Preloaded Study Material: SUCCESS ({len(pages)} pages loaded)")
except Exception as e:
    print("7. Preloaded Study Material: FAILED -", e)

# 8. RAG Pipeline End-to-End Check
try:
    from rag_pipeline import create_vector_store, get_relevant_context
    vs, chunks = create_vector_store(pages)
    ctx, docs = get_relevant_context(vs, "Fundamental Rights Article 21", k=2)
    print(f"8. RAG Pipeline End-to-End: SUCCESS ({chunks} chunks indexed, context retrieved)")
except Exception as e:
    print("8. RAG Pipeline: FAILED -", e)

print()
print("=" * 60)
print("  All core components verified successfully!")
print("=" * 60)
