# 🛡️ AEGIS Lite

**Your AI. Your Device. Your Data.**

A local-first, privacy-preserving personal AI assistant that remembers your life
and answers questions about it — running entirely on your own machine with
zero data sent to the internet.

> Built for IEEE NKSS Ideathon 2026 Grand Finale · Domain: Open Innovation

---

## What It Does

| Feature | Detail |
|---|---|
| **Local LLM** | Runs qwen2:0.5b or phi3:mini via Ollama — no cloud API |
| **Personal Memory** | Stores your notes, meetings, tasks, deadlines in local SQLite |
| **RAG Pipeline** | Retrieves relevant memory chunks and answers grounded questions |
| **Privacy First** | Zero network calls during inference — data never leaves your device |
| **Offline Capable** | Works with no internet after initial model download |

---

## Tech Stack

```
LLM           Ollama · qwen2:0.5b (dev) · phi3:mini (demo)
Embeddings    BAAI/bge-small-en-v1.5 · 384 dimensions · ~380 MB
Vector DB     LanceDB (embedded — no server needed)
Memory Store  SQLite with FTS5 full-text search
RAG           LlamaIndex-style retrieve → prompt → answer pipeline
UI            Streamlit
Language      Python 3.11
Platform      GitHub Codespaces
```

---

## Project Structure

```
aegis-lite/
├── .devcontainer/
│   └── devcontainer.json       # Codespaces auto-setup config
├── .github/
│   └── workflows/
│       └── verify.yml          # CI placeholder (optional)
├── aegis/
│   ├── config.py               # Central config — models, paths, RAG params
│   ├── memory/
│   │   ├── store.py            # SQLite episodic memory store
│   │   └── schema.sql          # DB schema with FTS5 index
│   ├── embeddings/
│   │   └── engine.py           # Local BGE-small embedding engine
│   ├── rag/
│   │   └── pipeline.py         # RAG pipeline — retrieve, prompt, answer
│   ├── llm/
│   │   └── interface.py        # Ollama LLM wrapper
│   └── ingest/
│       └── pipeline.py         # Text and file ingestion
├── ui/
│   └── app.py                  # Streamlit web UI
├── demo/
│   ├── demo.py                 # CLI demo script
│   └── create_sample_data.py   # Creates sample notes for demo
├── data/
│   ├── db/                     # SQLite database (auto-created)
│   ├── vectors/                # LanceDB vector index (auto-created)
│   └── sample_notes/           # Sample meeting notes, tasks, deadlines
├── setup.py                    # Makes aegis importable as a package
├── setup.sh                    # One-command setup for fresh Codespaces
└── requirements.txt            # Python dependencies
```

---

## Quick Start — GitHub Codespaces

### Step 1 — Open in Codespaces
Click **Code → Codespaces → Create codespace on main** in your GitHub repo.

The `devcontainer.json` runs `setup.sh` automatically.
Wait ~5 minutes for everything to install.

### Step 2 — If Setup Did Not Run Automatically
```bash
bash setup.sh
```

### Step 3 — Start Ollama (if not already running)
```bash
ollama serve &
sleep 5
```

### Step 4 — Run the UI
```bash
streamlit run ui/app.py --server.port 8501
```

Codespaces will show a popup — click **Open in Browser**.

---

## Running With Different Models

```bash
# qwen2:0.5b — fast, fits in 3GB RAM (recommended for Codespaces)
AEGIS_MODEL=qwen2:0.5b streamlit run ui/app.py

# phi3:mini — better quality, needs 8GB+ free RAM (recommended for demo day)
AEGIS_MODEL=phi3:mini streamlit run ui/app.py

# Use default from config.py
streamlit run ui/app.py
```

---

## Manual Setup (Without setup.sh)

If you prefer to set up step by step:

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install aegis as a package (fixes ModuleNotFoundError)
pip install -e .

# 3. Install Ollama binary
curl -fsSL https://ollama.com/install.sh | sh

# 4. Start Ollama server
ollama serve &
sleep 5

# 5. Pull the model
ollama pull qwen2:0.5b

# 6. Create sample data
python demo/create_sample_data.py

# 7. Run CLI demo to verify everything works
python demo/demo.py

# 8. Run the UI
streamlit run ui/app.py --server.port 8501
```

---

## Make Ollama Start Automatically

Run this once so Ollama starts every time a terminal opens:

```bash
echo 'ollama serve &>/tmp/ollama.log & sleep 8 && ollama run qwen2:0.5b "ready" &>/dev/null &' >> ~/.bashrc
source ~/.bashrc
```

---

## Verification Steps

Run these in order to confirm every component works:

### Memory Store
```bash
python -c "
from aegis.memory.store import MemoryStore
s = MemoryStore()
rid = s.add('Test record', kind='note', title='Test')
print('Added:', rid)
print('Count:', s.count())
s.delete(rid)
print('Deleted. Count:', s.count())
print('Memory store OK')
"
```

### Embedding Engine
```bash
python -c "
from aegis.embeddings.engine import embed_query
v = embed_query('what are my deadlines')
print('Vector dimensions:', len(v))
print('Embedding engine OK')
"
```

### LLM Interface
```bash
python -c "
from aegis.llm.interface import is_ollama_running, is_model_available, ask_llm
print('Ollama running:', is_ollama_running())
print('Model available:', is_model_available())
r = ask_llm('Say hello in one sentence.')
print('Response:', r[:80])
print('LLM OK')
"
```

### Full RAG Pipeline
```bash
python -c "
from aegis.memory.store import MemoryStore
from aegis.ingest.pipeline import ingest_text
from aegis.rag.pipeline import answer, build_index

store = MemoryStore()
ingest_text('Deadline: present at JCER Belagavi on July 17 at 9 AM.',
            kind='deadline', title='Finale', store=store)
result = answer('what are my deadlines', store)
print('Answer:', result['answer'])
print('Sources:', [s['title'] for s in result['sources']])
print('RAG pipeline OK')
"
```

### Full CLI Demo
```bash
python demo/demo.py
```

---

## How It Works

```
Your Notes / Meetings / Tasks
           ↓
    Embedding Model (local, ~380 MB)
           ↓
    Vector Database (LanceDB on disk)
           ↓
  Your Question → embed → search → top chunks
           ↓
    Local LLM (Ollama — localhost only)
           ↓
    Answer + Citations (from your memory)
```

**Nothing leaves your machine at any point.**

---

## Demo Flow (For Presentation)

**1. Show System Status (sidebar)**
> "Ollama running on localhost:11434.
> Embeddings on device. Database local SQLite.
> Zero network calls during inference."

**2. Add a Memory Live**
Go to Add Memory tab → select Meeting → paste:
```
Team sync today.
Decision: use qwen2:0.5b for demo.
Action item: Bharatesh to show RAG pipeline first.
```
Hit Save.

**3. Ask Questions**
Go to Ask AEGIS tab:
- *"What did we decide in today's sync?"*
- *"What are my action items?"*

Show the answer with source cards below.

**4. Show Memory Tab**
> "All your records — stored locally,
> visible only to you, never uploaded anywhere."

**5. Closing Line**
> "Everything you just saw happened on this machine.
> Nothing went to the internet.
> Your AI. Your Device. Your Data."

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ollama: command not found` | `curl -fsSL https://ollama.com/install.sh \| sh` |
| `ModuleNotFoundError: aegis` | `pip install -e .` then `cd` to project root |
| `LLM timed out` | Switch to `qwen2:0.5b` — phi3:mini needs more RAM |
| `No memory found` | Run `python demo/create_sample_data.py` then ingest files |
| `FTS5 syntax error` | Already fixed in store.py — special chars sanitized |
| `Chunks found: 0` | Similarity threshold — check `SIMILARITY_THRESHOLD` in pipeline.py |
| Streamlit port busy | Add `--server.port 8502` to the run command |

---

## Key Config Values

All in `aegis/config.py`:

```python
OLLAMA_MODEL     = "qwen2:0.5b"      # override with AEGIS_MODEL env var
EMBED_MODEL      = "BAAI/bge-small-en-v1.5"
TOP_K_RETRIEVE   = 2                  # chunks retrieved per query
SIMILARITY_THRESHOLD = 1.2            # LanceDB cosine distance cutoff
LLM_MAX_TOKENS   = 512
LLM_TEMPERATURE  = 0.1               # low = factual answers
```

---

## What Is NOT In This Project (By Design)

This is AEGIS **Lite** — a focused prototype. The following are out of scope:

- Biometric authentication
- Desktop automation
- Voice interface
- Multi-agent pipeline
- Knowledge graph / digital twin
- Cloud sync

These belong to the full AEGIS vision — future scope.

---

## Commit History Reference

```
chore: init repository structure
chore(devcontainer): add Codespaces config
chore(deps): add requirements.txt
feat(config): add central config
feat(db): add SQLite schema with FTS5
feat(memory): implement episodic memory store
feat(embeddings): add local BGE-small engine
feat(rag): implement RAG pipeline
feat(llm): add Ollama LLM interface
feat(ingest): add text and file ingest pipeline
feat(demo): add sample data and CLI demo
feat(ui): add Streamlit UI
fix(pkg): add setup.py for module resolution
fix(rag): add similarity threshold filter
fix(rag): increase threshold to 1.2 for BGE-small
fix(memory): sanitize FTS5 input to handle special chars
fix(llm): switch to qwen2:0.5b for Codespaces RAM constraints
fix(rag): rewrite prompt with instruction format
fix(ui): auto-rebuild vector index on startup
```

---

## About

Built as a proof of concept that powerful AI assistance and complete data privacy
are not mutually exclusive.

> *"Unlike ChatGPT, AEGIS never sends your data anywhere.
> Privacy is enforced architecturally, not by a privacy policy."*