"""
AEGIS Lite — CLI Demo Script
Run this to verify the full pipeline works before the presentation.
Shows judges (and yourself) that everything runs locally.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

from aegis.memory.store import MemoryStore
from aegis.ingest.pipeline import ingest_file, ingest_text
from aegis.rag.pipeline import build_index, answer
from aegis.llm.interface import is_ollama_running, is_model_available
from aegis.config import OLLAMA_MODEL, EMBED_MODEL

console = Console()


def check_system():
    """Step 1: Verify the system is ready."""
    console.print(Panel.fit(
        "[bold blue]AEGIS Lite — System Check[/bold blue]",
        border_style="blue"
    ))

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Status", style="bold")
    table.add_column("Component")
    table.add_column("Detail")

    # Ollama
    ollama_ok = is_ollama_running()
    table.add_row(
        "✅" if ollama_ok else "❌",
        "Ollama Server",
        "Running on localhost:11434" if ollama_ok else "NOT RUNNING — run: ollama serve",
    )

    # Model
    model_ok = is_model_available()
    table.add_row(
        "✅" if model_ok else "❌",
        f"LLM Model ({OLLAMA_MODEL})",
        "Available" if model_ok else f"NOT FOUND — run: ollama pull {OLLAMA_MODEL}",
    )

    # Embedding model note
    table.add_row("✅", f"Embedding Model", f"{EMBED_MODEL} (downloads on first use)")

    console.print(table)

    if not ollama_ok or not model_ok:
        console.print("\n[red]⚠️  Fix the issues above before running the demo.[/red]")
        return False

    console.print("\n[green]All systems ready.[/green]\n")
    return True


def load_sample_data(store: MemoryStore):
    """Step 2: Load sample data into memory."""
    console.print(Panel.fit(
        "[bold blue]Step 2: Loading Sample Memories[/bold blue]",
        border_style="blue"
    ))

    import os
    from pathlib import Path

    sample_dir = Path("data/sample_notes")
    if not sample_dir.exists():
        console.print("[yellow]Sample data not found. Running create_sample_data.py...[/yellow]")
        import subprocess
        subprocess.run(["python", "demo/create_sample_data.py"], check=True)

    # Determine file kinds
    file_kinds = {
        "meeting_monday.txt": "meeting",
        "project_tasks.txt": "task",
        "deadlines.txt": "deadline",
    }

    loaded = 0
    for filename, kind in file_kinds.items():
        path = sample_dir / filename
        if path.exists():
            result = ingest_file(str(path), kind=kind, store=store)
            status = "✅" if result["success"] else "❌"
            console.print(f"  {status} {filename} ({kind})")
            if result["success"]:
                loaded += 1

    console.print(f"\n[green]{loaded} files loaded. Total records: {store.count()}[/green]\n")
    return loaded > 0


def run_rag_demo(store: MemoryStore):
    """Step 3: Run RAG queries and show results."""
    console.print(Panel.fit(
        "[bold blue]Step 3: RAG Pipeline Demo[/bold blue]",
        border_style="blue"
    ))

    questions = [
        "What are my action items from Monday's meeting?",
        "What are the deadlines coming up?",
        "What tasks are high priority?",
        "When is the AEGIS Lite prototype due?",
        "What should I bring to the finale?",
    ]

    for i, question in enumerate(questions, 1):
        console.print(f"\n[bold cyan]Q{i}: {question}[/bold cyan]")
        console.print("[dim]Searching memory and generating answer...[/dim]")

        result = answer(question, store)

        console.print(Panel(
            result["answer"],
            title="[green]Answer[/green]",
            border_style="green",
        ))

        if result["sources"]:
            console.print("[dim]Sources used:[/dim]")
            for src in result["sources"][:2]:
                console.print(f"  • {src['title']} ({src['kind']})")

        console.print()


def main():
    console.print(Panel(
        "[bold white]AEGIS Lite[/bold white]\n"
        "[italic]Your AI. Your Device. Your Data.[/italic]\n\n"
        "[dim]Prototype Demo — IEEE NKSS Ideathon 2026[/dim]",
        border_style="blue",
        padding=(1, 4),
    ))

    # Step 1: System check
    if not check_system():
        return

    # Step 2: Load data
    store = MemoryStore()
    if store.count() == 0:
        ok = load_sample_data(store)
        if not ok:
            console.print("[red]Failed to load sample data.[/red]")
            return
    else:
        console.print(f"[green]Using existing memory: {store.count()} records[/green]\n")

    # Step 3: RAG demo
    run_rag_demo(store)

    console.print(Panel.fit(
        "[bold green]✓ Demo complete — all processing ran locally.[/bold green]\n"
        "[dim]Now run: streamlit run ui/app.py[/dim]",
        border_style="green",
    ))


if __name__ == "__main__":
    main()