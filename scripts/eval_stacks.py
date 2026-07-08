"""Real evals for stacks: ingest throughput, retrieval accuracy, and
end-to-end query latency -- no mocks, matching this portfolio's eval
discipline throughout (private-agent's eval_agent.py, lantern's
eval_lantern.py).

Usage: python3 scripts/eval_stacks.py
"""

import shutil
import statistics
import tempfile
import time
from pathlib import Path

from stacks.generator import generate_answer
from stacks.index import Index
from stacks.ingest import ingest_path
from stacks.retriever import retrieve

DOCS = {
    "handbook.md": (
        "# Company Handbook\n\n"
        "## Vacation Policy\n"
        "Employees accrue 15 days of paid vacation per year, credited monthly "
        "at 1.25 days per month.\n\n"
        "## Remote Work\n"
        "Employees may work remotely up to 3 days per week with manager approval."
    ),
    "recipe.txt": (
        "Simple tomato soup: saute one diced onion in olive oil, add two cans "
        "of crushed tomatoes and a cup of vegetable stock, simmer 20 minutes, "
        "blend smooth, stir in cream."
    ),
    "meeting_notes.md": (
        "# Q3 Planning Meeting\n\n"
        "Attendees discussed the roadmap for Q3, prioritizing the mobile app "
        "redesign over the API v2 migration. Budget approved: $45,000."
    ),
}

# (question, expected keyword in the answer, expected source filename)
QUERIES = [
    ("how many vacation days do employees get", "15", "handbook.md"),
    ("how do I make tomato soup", "onion", "recipe.txt"),
    ("what was the Q3 budget", "45,000", "meeting_notes.md"),
]


def run() -> None:
    tmpdir = Path(tempfile.mkdtemp())
    index_path = tmpdir / "eval_index.json"
    docs_dir = tmpdir / "docs"
    docs_dir.mkdir()
    for name, content in DOCS.items():
        (docs_dir / name).write_text(content)

    idx = Index(path=index_path)

    print("stacks eval\n")

    start = time.monotonic()
    result = ingest_path(docs_dir, index=idx)
    ingest_elapsed = time.monotonic() - start
    print(f"Ingest: {len(DOCS)} files, {result['total_chunks']} chunks in {ingest_elapsed:.2f}s\n")

    latencies = []
    correct_keyword = 0
    correct_source = 0

    for question, expected_keyword, expected_source in QUERIES:
        start = time.monotonic()
        results = retrieve(question, index=idx, top_k=3)
        answer = generate_answer(question, results)
        elapsed = time.monotonic() - start
        latencies.append(elapsed)

        keyword_hit = expected_keyword.lower() in answer.text.lower()
        source_hit = any(expected_source in c.source_file for c in answer.citations)
        correct_keyword += int(keyword_hit)
        correct_source += int(source_hit)

        print(f"[{elapsed:.2f}s] Q: {question}")
        print(f"  A: {answer.text}")
        print(f"  expected keyword {expected_keyword!r}: {'yes' if keyword_hit else 'NO'}, "
              f"cited {expected_source}: {'yes' if source_hit else 'NO'}\n")

    print("--- summary (measured, this run, this machine) ---")
    print(f"Ingest: {result['total_chunks']} chunks in {ingest_elapsed:.2f}s "
          f"({ingest_elapsed / result['total_chunks']:.2f}s/chunk)")
    print(f"Query latency -- median: {statistics.median(latencies):.2f}s, "
          f"range: {min(latencies):.2f}s-{max(latencies):.2f}s")
    print(f"Correct keyword in answer: {correct_keyword}/{len(QUERIES)}")
    print(f"Correct source cited: {correct_source}/{len(QUERIES)}")

    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    run()
