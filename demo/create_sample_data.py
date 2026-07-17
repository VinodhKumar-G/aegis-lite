"""
Creates sample data files for the demo.
Run this once: python demo/create_sample_data.py
"""

from pathlib import Path

samples = {
    "meeting_monday.txt": """Team Standup - Monday July 14, 2026

Attendees: Bharatesh, Rohan, Priya

Discussion:
- AEGIS Lite prototype is on track for the July 17 finale
- RAG pipeline working end-to-end on Codespaces
- UI needs polish on the sources panel

Decisions:
- Use phi3:mini model for the demo (faster on shared hardware)
- Streamlit chosen as UI framework
- Demo will use 3 pre-loaded sample memories + 1 live add

Action items:
- Bharatesh: finalize RAG pipeline by July 15
- Rohan: prepare slide deck talking points by July 15
- Priya: write demo script with 5 example questions by July 16
- Team: rehearse full 7-minute demo on July 16 evening
""",

    "project_tasks.txt": """Project AEGIS Lite - Active Tasks

HIGH PRIORITY:
- Complete vector database integration with LanceDB [Bharatesh] [Due: July 15]
- Test RAG pipeline with 20+ memory records [Team] [Due: July 15]
- Create judge demo script [Priya] [Due: July 16]

MEDIUM PRIORITY:
- Add file upload support to Streamlit UI [Rohan] [Due: July 16]
- Write README with setup instructions [Bharatesh] [Due: July 16]
- Record 2-minute video walkthrough as backup [Team] [Due: July 16]

DONE:
- Set up GitHub Codespaces devcontainer [Done July 12]
- Install Ollama and pull phi3:mini [Done July 12]
- Build memory store with SQLite [Done July 13]
""",

    "deadlines.txt": """Important Deadlines - July 2026

1. IEEE NKSS Ideathon Grand Finale
   Date: July 17, 2026
   Venue: JCER, Belagavi
   Reporting time: 9:00 AM
   Presentation: 5-7 minutes + Q&A 3-5 minutes
   What to bring: College ID, Laptop (fully charged), Demo running

2. AEGIS Lite Prototype Completion
   Date: July 15, 2026
   Owner: Bharatesh
   Deliverable: Working Codespaces demo with RAG pipeline

3. Demo Rehearsal
   Date: July 16, 2026 - 6 PM
   Location: [Your college lab / meet link]
   Duration: 2 hours - full run-through

4. Registration Fee Payment
   Amount: Rs. 200 per person (IEEE Member) / Rs. 250 (Non-Member)
   Pay at: JCER registration desk on July 17
""",
}

output_dir = Path("data/sample_notes")
output_dir.mkdir(parents=True, exist_ok=True)

for filename, content in samples.items():
    (output_dir / filename).write_text(content)
    print(f"✓ Created: data/sample_notes/{filename}")

print("\nSample data created. Now run: python demo/demo.py")