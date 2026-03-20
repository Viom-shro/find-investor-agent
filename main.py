from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from investor_agent.agent import InvestorDataAgent


def main() -> int:
    parser = argparse.ArgumentParser(description="Find investor info and save to CSV.")
    parser.add_argument(
        "query",
        type=str,
        help='Example: "Fintech investors in India investing $500k–$2M"',
    )
    parser.add_argument("--max-results", type=int, default=8, help="How many search results to scan.")
    parser.add_argument("--max-pages", type=int, default=None, help="Hard cap on fetched pages.")
    parser.add_argument("--sleep-s", type=float, default=1.0, help="Delay between page fetch/extract.")
    parser.add_argument("--output-csv", type=str, default=None, help="Output CSV path.")
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "gemini"],
        default=None,
        help="Force LLM provider (if both keys exist).",
    )
    parser.add_argument("--max-page-chars", type=int, default=12000, help="Truncate page text for LLM.")
    parser.add_argument("--print-only", action="store_true", help="Do not write CSV, only print records JSON.")

    args = parser.parse_args()

    agent = InvestorDataAgent(output_csv=args.output_csv, sleep_s=args.sleep_s)
    records: list[dict[str, Any]] = agent.run(
        args.query,
        max_results=args.max_results,
        max_pages=args.max_pages,
        provider=args.provider,
        user_agent_max_chars=args.max_page_chars,
    )

    if args.print_only:
        print(json.dumps(records, ensure_ascii=False, indent=2))
    else:
        print(f"Saved {len(records)} records to CSV.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

