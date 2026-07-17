"""
AEGIS Lite — Streamlit Web UI
A clean, simple interface demonstrating:
  - Adding personal memories (notes, meetings, tasks, deadlines)
  - Asking questions answered from local memory (RAG)
  - Viewing stored memories
  - System status (proves everything is local)
"""

import streamlit as st
import time
from pathlib import Path

from aegis.config import (
    APP_TITLE,
    APP_SLOGAN,
    OLLAMA_MODEL,
    EMBED_MODEL,
)
from aegis.memory.store import MemoryStore
from aegis.llm.interface import is_ollama_running, is_model_available
from aegis.ingest.pipeline import ingest_text
from aegis.rag.pipeline import answer, build_index


# ── Page Config ────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1a1a2e;
        margin-bottom: 0;
    }
    .slogan {
        font-size: 1.1rem;
        color: #006699;
        font-style: italic;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    .privacy-badge {
        background-color: #e8f5e9;
        border: 1px solid #4caf50;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 0.85rem;
        color: #2e7d32;
        display: inline-block;
        margin-bottom: 1rem;
    }
    .source-card {
        background-color: #f0f7ff;
        border-left: 3px solid #006699;
        padding: 8px 12px;
        margin: 4px 0;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .answer-box {
        background-color: #fafafa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)


# ── Init ───────────────────────────────────────────────────────────────────────

@st.cache_resource
def get_store():
    return MemoryStore()

store = get_store()
# ── Auto-rebuild index on startup if records exist ──────────────
@st.cache_resource
def ensure_index_built():
    from aegis.rag.pipeline import build_index, get_vector_db
    db = get_vector_db()
    if "memory_chunks" not in db.table_names() and store.count() > 0:
        print("Index missing — rebuilding on startup...")
        build_index(store)
    return True

ensure_index_built()


# ── Sidebar — System Status ────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🛡️ AEGIS Lite")
    st.markdown(f"*{APP_SLOGAN}*")
    st.divider()

    st.markdown("#### System Status")

    # Ollama status
    ollama_ok = is_ollama_running()
    st.markdown(
        f"{'🟢' if ollama_ok else '🔴'} **Ollama Server** "
        f"({'Running' if ollama_ok else 'Offline'})"
    )

    # Model status
    model_ok = is_model_available()
    st.markdown(
        f"{'🟢' if model_ok else '🔴'} **LLM Model** "
        f"(`{OLLAMA_MODEL}`)"
    )

    # Memory count
    count = store.count()
    st.markdown(f"🟢 **Memory Records** ({count} stored)")

    st.divider()

    # Privacy proof
    st.markdown("#### 🔒 Privacy Proof")
    st.markdown("""
    **All processing is local:**
    - LLM: `localhost:11434`
    - Embeddings: on-device
    - Database: local SQLite
    - **Zero network calls** during inference
    """)

    st.divider()

    st.markdown("#### Quick Rebuild")
    if st.button("🔄 Rebuild Vector Index", use_container_width=True):
        with st.spinner("Rebuilding..."):
            build_index(store)
        st.success("Index rebuilt!")


# ── Header ─────────────────────────────────────────────────────────────────────

st.markdown('<div class="main-title">🛡️ AEGIS Lite</div>', unsafe_allow_html=True)
st.markdown(f'<div class="slogan">{APP_SLOGAN}</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="privacy-badge">'
    '🔒 100% Local · No Cloud · No Data Leaves This Device'
    '</div>',
    unsafe_allow_html=True,
)


# ── Tabs ───────────────────────────────────────────────────────────────────────

tab_ask, tab_add, tab_memory = st.tabs([
    "💬 Ask AEGIS",
    "➕ Add Memory",
    "📚 View Memory",
])


# ── Tab 1: Ask AEGIS ──────────────────────────────────────────────────────────

with tab_ask:
    st.markdown("### Ask a question about your life")
    st.markdown(
        "AEGIS answers from **your personal memory only** — "
        "not from the internet or its training data."
    )

    # Example questions
    with st.expander("💡 Example questions to try"):
        examples = [
            "What did I commit to in my last meeting?",
            "What are my deadlines this week?",
            "What tasks are pending for Project Alpha?",
            "What is my current role?",
            "Summarize my recent meeting notes.",
            "What are the action items from Monday?",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{ex}"):
                st.session_state["query_input"] = ex

    # Query input
    query = st.text_input(
        "Your question:",
        value=st.session_state.get("query_input", ""),
        placeholder="e.g. What did I commit to last Monday?",
        key="query_box",
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        ask_btn = st.button("Ask →", type="primary", use_container_width=True)

    if ask_btn and query:
        if count == 0:
            st.warning(
                "⚠️ Your memory is empty. "
                "Go to the **Add Memory** tab and add some notes first."
            )
        else:
            with st.spinner("🧠 Searching your memory and generating answer..."):
                start = time.time()
                result = answer(query, store)
                elapsed = time.time() - start

            # Show answer
            st.markdown("#### Answer")
            st.markdown(
                f'<div class="answer-box">{result["answer"]}</div>',
                unsafe_allow_html=True,
            )

            # Performance note
            st.caption(f"⏱️ Generated in {elapsed:.1f}s · Processed entirely on this device")

            # Show sources
            if result["sources"]:
                st.markdown("#### Sources Retrieved from Your Memory")
                for i, src in enumerate(result["sources"], 1):
                    import re
                    # Strip [KIND] prefix from chunk preview
                    clean_chunk = re.sub(r'^\[.*?\]\s*', '', src["chunk"])

                    st.markdown(
                        f'<div class="source-card">'
                        f'<strong>Source {i}: {src["title"]}</strong> '
                        f'<em>({src["kind"]})</em><br>'
                        f'{clean_chunk}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.info("No matching memories found. Add more records and rebuild the index.")

    elif ask_btn and not query:
        st.warning("Please enter a question.")


# ── Tab 2: Add Memory ─────────────────────────────────────────────────────────

with tab_add:
    st.markdown("### Add to Your Personal Memory")
    st.markdown(
        "Everything you add is stored **locally** in an encrypted SQLite database. "
        "Nothing is sent anywhere."
    )

    col_left, col_right = st.columns(2)

    with col_left:
        kind = st.selectbox(
            "Memory type:",
            options=["note", "meeting", "task", "deadline"],
            format_func=lambda x: {
                "note": "📝 Note",
                "meeting": "🤝 Meeting",
                "task": "✅ Task",
                "deadline": "⏰ Deadline",
            }[x],
        )

        title = st.text_input(
            "Title (optional):",
            placeholder="e.g. Monday Standup - July 14",
        )

    with col_right:
        st.markdown("**Quick templates:**")
        templates = {
            "Meeting Notes": (
                "meeting",
                "Team Meeting - [Date]",
                "Attendees: [names]\n\nDiscussion:\n- \n\nDecisions:\n- \n\nAction items:\n- [Name]: [task] by [date]\n",
            ),
            "Task": (
                "task",
                "Task: [Title]",
                "Description: \nAssigned to: Me\nDue date: \nProject: \nPriority: High/Medium/Low\n",
            ),
            "Deadline": (
                "deadline",
                "Deadline: [What]",
                "Deadline: \nDue: \nProject: \nNotes: \n",
            ),
        }
        for label, (t_kind, t_title, t_content) in templates.items():
            if st.button(f"Use {label} template", key=f"tpl_{label}"):
                st.session_state["tpl_kind"] = t_kind
                st.session_state["tpl_title"] = t_title
                st.session_state["tpl_content"] = t_content

    content = st.text_area(
        "Content:",
        value=st.session_state.get("tpl_content", ""),
        height=200,
        placeholder=(
            "Example (Meeting):\n"
            "Attendees: Bharatesh, Teammate\n"
            "Discussed: AEGIS Lite prototype scope\n"
            "Decisions: Use phi3:mini for demo, Streamlit for UI\n"
            "Action items:\n"
            "- Bharatesh: complete RAG pipeline by July 10\n"
            "- Teammate: prepare demo script by July 12"
        ),
    )

    tags_input = st.text_input(
        "Tags (comma-separated, optional):",
        placeholder="e.g. project-aegis, urgent, team",
    )
    tags = [t.strip() for t in tags_input.split(",") if t.strip()]

    if st.button("💾 Save to Memory", type="primary"):
        if not content.strip():
            st.error("Content cannot be empty.")
        else:
            with st.spinner("Saving and rebuilding index..."):
                result = ingest_text(
                    content=content,
                    kind=kind,
                    title=title,
                    tags=tags,
                    store=store,
                    rebuild_index=True,
                )

            if result["success"]:
                st.success(result["message"])
                # Clear template cache
                for key in ["tpl_kind", "tpl_title", "tpl_content"]:
                    st.session_state.pop(key, None)
                st.rerun()
            else:
                st.error(result["message"])

    # File upload
    st.divider()
    st.markdown("#### Or upload a .txt / .md file")
    uploaded = st.file_uploader(
        "Upload file",
        type=["txt", "md"],
        help="Text files are processed locally — no upload to any server.",
    )
    if uploaded:
        content_bytes = uploaded.read().decode("utf-8")
        file_title = Path(uploaded.name).stem.replace("_", " ").title()
        if st.button("💾 Save File to Memory"):
            with st.spinner("Ingesting file..."):
                result = ingest_text(
                    content=content_bytes,
                    kind="note",
                    title=file_title,
                    store=store,
                    rebuild_index=True,
                )
            if result["success"]:
                st.success(result["message"])
                st.rerun()
            else:
                st.error(result["message"])


# ── Tab 3: View Memory ────────────────────────────────────────────────────────

with tab_memory:
    st.markdown("### Your Personal Memory")
    st.markdown(f"**{count} records** stored locally on this device.")

    if count == 0:
        st.info("No memories yet. Go to **Add Memory** to get started.")
    else:
        # Filter
        filter_kind = st.selectbox(
            "Filter by type:",
            options=["all", "note", "meeting", "task", "deadline"],
        )

        records = store.get_all(
            kind=None if filter_kind == "all" else filter_kind
        )

        kind_icons = {
            "note": "📝",
            "meeting": "🤝",
            "task": "✅",
            "deadline": "⏰",
        }

        for record in records:
            icon = kind_icons.get(record["kind"], "📄")
            with st.expander(
                f"{icon} {record['title']} — {record['kind'].upper()}"
            ):
                st.text(record["content"])
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    import datetime
                    ts = datetime.datetime.fromtimestamp(record["created_at"])
                    st.caption(f"Added: {ts.strftime('%Y-%m-%d %H:%M')}")
                with col_b:
                    if st.button("🗑️ Delete", key=f"del_{record['id']}"):
                        store.delete(record["id"])
                        build_index(store)
                        st.rerun()