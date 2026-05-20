import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
HF_TOKEN          = os.getenv("HF_TOKEN", "")

# LLM: "hf" | "anthropic" | "openai" | "mock"
LLM_PROVIDER   = "hf"
HF_MODEL       = "Qwen/Qwen2.5-7B-Instruct"   # gemma-2-2b-it needs provider enablement; Qwen works on free tier
LLM_MODEL      = "claude-sonnet-4-6"      # fallback if provider != hf

EMBEDDING_MODEL    = "all-MiniLM-L6-v2"
COLLECTION_NAME    = "enterprise_rag"

CHUNK_SIZE         = 300
CHUNK_OVERLAP      = 50
TOP_K_RETRIEVE     = 10
TOP_K_FINAL        = 5
SIMILARITY_THRESHOLD = 0.25
