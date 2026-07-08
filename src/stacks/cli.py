"""CLI entrypoint: `stacks ingest <path>` and `stacks ask <question>`."""

import argparse

from stacks.generator import generate_answer
from stacks.ingest import ingest_path
from stacks.retriever import retrieve


def main() -> None:
    parser = argparse.ArgumentParser(prog="stacks")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Index a file or directory")
    ingest_parser.add_argument("path", help="Path to a file or directory to index")

    ask_parser = subparsers.add_parser("ask", help="Ask a question over indexed files")
    ask_parser.add_argument("question", help="The question to ask")
    ask_parser.add_argument("--top-k", type=int, default=5)

    args = parser.parse_args()

    if args.command == "ingest":
        result = ingest_path(args.path)
        print(f"Indexed {len(result['indexed_files'])} file(s), {result['total_chunks']} chunks.")
        if result["skipped_files"]:
            print(f"Skipped {len(result['skipped_files'])} file(s) (empty or unreadable).")
        print(f"Index now has {result['index_size']} total chunks.")

    elif args.command == "ask":
        results = retrieve(args.question, top_k=args.top_k)
        answer = generate_answer(args.question, results)
        print(answer.text)
        if answer.citations:
            print("\nSources:")
            for c in answer.citations:
                print(f"  - {c.source_file} (page {c.page})")


if __name__ == "__main__":
    main()
