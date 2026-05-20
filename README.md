---
title: NexusRAG — Enterprise Intelligence
emoji: 🔐
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
app_port: 7860
---

# 🔐 NexusRAG — Enterprise Intelligence

A production-grade **Retrieval-Augmented Generation (RAG)** system for enterprise knowledge management, featuring role-based access control, hybrid search, AI-powered off-topic detection, and a polished Chainlit chat UI.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Multi-source ingestion** | PDFs · CSV · JSON system logs |
| **Hybrid retrieval** | ChromaDB semantic search + BM25 re-ranking |
| **RBAC** | 5 roles × 7 department scopes, enforced at retrieval |
| **AI off-topic guard** | Embedding cosine similarity vs KB — no hardcoded regex |
| **Citation tracing** | Every answer cites `[Source N]` with file + dept + score |
| **Confidence scoring** | Per-answer HIGH / MEDIUM / LOW with percentage |
| **LLM** | Qwen/Qwen2.5-7B-Instruct via HuggingFace Inference API |
| **UI** | Chainlit 2.x · dark/light theme · quick-login panel |

---

## 🏗️ Architecture

```
User query
    │
    ▼
Off-topic guard ──── embedding cosine similarity vs KB
    │ pass
    ▼
RBAC check ──────── roles.json × users.json → allowed departments
    │ allow
    ▼
Hybrid Retriever
  ├─ ChromaDB semantic search  (all-MiniLM-L6-v2, cosine space)
  ├─ Similarity threshold filter  (score ≥ 0.25)
  ├─ Preferred-department boost   (query-keyword → dept × 1.30)
  └─ BM25 re-rank  (0.6 × semantic + 0.4 × BM25)
    │
    ▼
Qwen2.5-7B-Instruct  (HuggingFace Inference API)
  └─ Grounded prompt: cite [Source N], no hallucination
    │
    ▼
Chainlit UI  ─  answer + citations + confidence + role badge
```

---

## 👥 Demo Users

| User | Password | Role | Access |
|---|---|---|---|
| `alice` | `alice123` | admin | All departments |
| `bob` | `bob123` | hr_staff | HR + employees |
| `carol` | `carol123` | finance | Finance + employees |
| `dave` | `dave123` | it_ops | IT + logs + incidents |
| `eve` | `eve123` | employee | HR only |

Quick-login buttons are available on the sign-in screen.

---

## 🚀 Local Setup

```bash
git clone https://github.com/<your-username>/nexusrag
cd nexusrag

pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and fill in HF_TOKEN and CHAINLIT_AUTH_SECRET

# Generate synthetic enterprise dataset (first run only)
python generate_dataset.py

# Launch
chainlit run app.py --host 0.0.0.0 --port 8000
```

Open **http://localhost:8000** and log in with any demo credential.

> **Note:** The knowledge base is auto-ingested the first time the app starts (or when ChromaDB is empty). This takes ~30 seconds on CPU.

---

## ☁️ HuggingFace Spaces

Set the following **Space Secrets** in your HF Space settings:

| Secret | Value |
|---|---|
| `HF_TOKEN` | Your HuggingFace API token |
| `CHAINLIT_AUTH_SECRET` | Run `chainlit create-secret` to generate |

The Docker image auto-ingests the knowledge base on first boot.

---

## 📁 Project Structure

```
enterprise_rag/
├── app.py                  # Chainlit UI + auth + message routing
├── config.py               # Central configuration
├── generate_dataset.py     # Synthetic data generator (PDFs, CSV, JSON)
├── ingest_all.py           # Standalone ingestion script
├── requirements.txt
├── Dockerfile
│
├── rag/
│   ├── pipeline.py         # EnterprisePipeline orchestrator
│   ├── retriever.py        # HybridRetriever (semantic + BM25)
│   ├── generator.py        # LLM answer generation + citations
│   ├── vector_store.py     # ChromaDB wrapper (cosine similarity)
│   ├── embedder.py         # Sentence-transformer singleton
│   ├── ingestor.py         # PDF / CSV / JSON loaders
│   ├── rbac.py             # Role-based access control
│   └── off_topic_guard.py  # AI relevance guard
│
├── data/
│   ├── documents/          # hr_policy.pdf · finance_report.pdf · it_security.pdf
│   ├── structured/         # employees.csv · incidents.csv
│   ├── logs/               # system_logs.json
│   └── access_control/     # users.json · roles.json
│
└── public/
    ├── custom.js           # Quick-login + sample-query buttons
    └── custom.css          # NexusRAG theme styles
```

---

## ⚙️ Configuration

Key settings in [`config.py`](config.py):

| Setting | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `"hf"` | `hf` · `openai` · `anthropic` · `mock` |
| `HF_MODEL` | `Qwen/Qwen2.5-7B-Instruct` | HuggingFace model ID |
| `SIMILARITY_THRESHOLD` | `0.25` | Minimum cosine similarity for retrieval |
| `TOP_K_RETRIEVE` | `10` | Candidates fetched from ChromaDB |
| `TOP_K_FINAL` | `5` | Chunks passed to LLM after BM25 re-rank |

---

## 🛡️ Security Notes

- Passwords in `USERS` dict are demo-only — replace with a proper auth provider for production
- The `.env` file is git-ignored; never commit real credentials
- RBAC is enforced both at query routing **and** at chunk retrieval (belt-and-suspenders)

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.
