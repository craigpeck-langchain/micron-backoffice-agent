"""Replay the 50 synthetic fixture emails through the compiled graph.

This seeds the LangSmith project that Engine mines: every run gets a stable
`run_name` (per scenario) and metadata (doc type, planted flaw, fixture id),
and every run whose fixture carries a planted flaw gets an explicit negative
`known_issue` feedback score - feedback is Engine's highest-priority signal.

    uv run python scripts/populate_traces.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)
os.environ["APP_ENV"] = "replay"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from backoffice_agent.graph import graph  # noqa: E402
from langchain_core.tracers.context import collect_runs  # noqa: E402
from langsmith import Client  # noqa: E402

FIXTURES_DIR = ROOT / "fixtures" / "emails"


def format_email(email: dict) -> str:
    return f"From: {email['from']}\nSubject: {email['subject']}\n\n{email['body']}"


def load_fixtures() -> list[dict]:
    files = sorted(p for p in FIXTURES_DIR.glob("*.json") if p.name != "index.json")
    return [json.loads(p.read_text(encoding="utf-8")) for p in files]


def main() -> None:
    client = Client()
    fixtures = load_fixtures()
    print(f"Replaying {len(fixtures)} fixture emails...")

    for i, fixture in enumerate(fixtures, start=1):
        email_text = format_email(fixture["email"])
        metadata = {
            "scenario": fixture["scenario"],
            "doc_type_expected": fixture["doc_type_expected"],
            "planted_flaw": fixture["planted_flaw"] or "none",
            "fixture_id": fixture["id"],
        }
        with collect_runs() as cb:
            try:
                graph.invoke(
                    {"messages": [{"role": "user", "content": email_text}]},
                    config={"tags": ["replay", "populate_traces"], "metadata": metadata},
                )
            except Exception as exc:  # noqa: BLE001 - keep going through the batch
                print(f"  [{i}/{len(fixtures)}] {fixture['scenario']}: ERROR {exc}")
                continue

        root_run = cb.traced_runs[0] if cb.traced_runs else None
        if root_run is not None and fixture["planted_flaw"]:
            client.create_feedback(
                root_run.id,
                key="known_issue",
                score=0,
                trace_id=root_run.id,
                comment=f"Planted flaw: {fixture['planted_flaw']} (scenario: {fixture['scenario']})",
            )
        run_id = root_run.id if root_run else "?"
        print(f"  [{i}/{len(fixtures)}] {fixture['scenario']} -> run {run_id}")

    print("Done. Traces are in LANGSMITH_PROJECT; check the Engine tab once analysis completes.")


if __name__ == "__main__":
    main()
