"""Export / restore the golden LangSmith dataset to/from a committed JSON snapshot.

    # recreate the dataset in LangSmith from its committed snapshot
    uv run python evals/dataset_snapshot.py restore golden
    uv run python evals/dataset_snapshot.py restore golden --reset    # overwrite if exists

    # pull the live dataset back down into its snapshot
    uv run python evals/dataset_snapshot.py export golden

The snapshot is committed so the dataset survives deletions and produces a
reproducible baseline for demo practice - no waiting on Engine to regenerate it.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

load_dotenv(override=True)

HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class DatasetConfig:
    name: str
    path: Path


DATASETS = {
    "golden": DatasetConfig("micron-backoffice-golden", HERE / "dataset_golden.json"),
}


def export_dataset(name: str, path: Path) -> None:
    client = Client()
    ds = client.read_dataset(dataset_name=name)
    examples = list(client.list_examples(dataset_id=ds.id))
    payload = {
        "name": ds.name,
        "description": ds.description or "",
        "examples": [
            {"inputs": ex.inputs, "outputs": ex.outputs, "metadata": ex.metadata or {}} for ex in examples
        ],
    }
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"Exported {len(examples)} examples from {ds.name!r} to {path}")


def restore_dataset(path: Path, reset: bool) -> None:
    if not path.is_file():
        raise SystemExit(f"Snapshot not found at {path}. Run `dataset_snapshot.py export` first.")

    payload = json.loads(path.read_text(encoding="utf-8"))
    name = payload["name"]
    description = payload.get("description") or ""
    examples = payload.get("examples", [])

    client = Client()
    existing = list(client.list_datasets(dataset_name=name))
    if existing:
        if not reset:
            print(f"Dataset {name!r} already exists in LangSmith. Pass --reset to delete and recreate it.")
            return
        print(f"Deleting existing dataset {name!r}...")
        client.delete_dataset(dataset_name=name)

    ds = client.create_dataset(dataset_name=name, description=description)
    print(f"Created dataset {ds.name} ({ds.id})")

    if not examples:
        print("Snapshot has no examples; dataset created empty.")
        return

    client.create_examples(
        dataset_id=ds.id,
        examples=[
            {"inputs": ex.get("inputs", {}), "outputs": ex.get("outputs", {}), "metadata": ex.get("metadata", {}) or {}}
            for ex in examples
        ],
    )
    print(f"Restored {len(examples)} examples.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=("export", "restore"))
    parser.add_argument("dataset_choice", choices=sorted(DATASETS))
    parser.add_argument("--name", default=None)
    parser.add_argument("--path", type=Path, default=None)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    config = DATASETS[args.dataset_choice]
    name = args.name or config.name
    path = args.path or config.path

    if args.mode == "export":
        if args.reset:
            print("--reset is ignored in export mode.")
        export_dataset(name, path)
    else:
        restore_dataset(path, args.reset)


if __name__ == "__main__":
    main()
