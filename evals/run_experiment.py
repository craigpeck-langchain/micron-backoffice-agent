"""Run an offline evaluation experiment against the golden dataset.

    uv run python evals/run_experiment.py golden

Prints CI-parseable lines (EXPERIMENT_NAME=, EXPERIMENT_URL=, ...) on completion.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "evals"))

from backoffice_agent.graph import graph  # noqa: E402
from evaluators import expected_behavior_evaluator, hallucination_evaluator  # noqa: E402
from langsmith import Client, aevaluate  # noqa: E402

EVALUATOR_REGISTRY = {
    "hallucination": hallucination_evaluator,
    "expected_behavior": expected_behavior_evaluator,
}


@dataclass(frozen=True)
class DatasetConfig:
    dataset: str
    evaluators: list[str]
    experiment_prefix: str


DATASETS = {
    "golden": DatasetConfig(
        dataset="micron-backoffice-golden",
        evaluators=["hallucination", "expected_behavior"],
        experiment_prefix="micron-backoffice",
    ),
}


async def target(inputs: dict) -> dict:
    return await graph.ainvoke(inputs)


def _parse_metadata(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise SystemExit(f"--metadata expects key=value, got {item!r}")
        k, v = item.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def _print_experiment_link(dataset: str, experiment_name: str) -> None:
    import os

    client = Client()
    try:
        ds = client.read_dataset(dataset_name=dataset)
    except Exception as exc:  # noqa: BLE001
        print(f"EXPERIMENT_NAME={experiment_name}")
        print(f"# Could not resolve dataset URL: {exc}")
        return

    workspace_id = os.getenv("LANGSMITH_WORKSPACE_ID", "").strip()
    base = "https://smith.langchain.com"
    url = f"{base}/o/{workspace_id}/datasets/{ds.id}/compare" if workspace_id else f"{base}/datasets/{ds.id}/compare"

    print(f"EXPERIMENT_NAME={experiment_name}")
    print(f"EXPERIMENT_URL={url}")
    print(f"DATASET_NAME={dataset}")
    print(f"DATASET_ID={ds.id}")


async def run(dataset: str, experiment_prefix: str, max_concurrency: int, metadata: dict[str, str], evaluators: list[str]) -> None:
    evaluator_fns = [EVALUATOR_REGISTRY[name] for name in evaluators]
    results = await aevaluate(
        target,
        data=dataset,
        evaluators=evaluator_fns,
        experiment_prefix=experiment_prefix,
        max_concurrency=max_concurrency,
        metadata=metadata or None,
    )
    print()
    _print_experiment_link(dataset, results.experiment_name)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dataset_choice", choices=sorted(DATASETS), help="Which dataset to run against.")
    parser.add_argument("--dataset", default=None, help="Override the dataset name.")
    parser.add_argument("--experiment-prefix", default=None)
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--metadata", action="append", default=[], metavar="KEY=VALUE")
    parser.add_argument("--evaluator", action="append", default=None, choices=sorted(EVALUATOR_REGISTRY))
    args = parser.parse_args()

    config = DATASETS[args.dataset_choice]
    dataset = args.dataset or config.dataset
    experiment_prefix = args.experiment_prefix or config.experiment_prefix
    evaluators = args.evaluator or config.evaluators

    asyncio.run(run(dataset, experiment_prefix, args.max_concurrency, _parse_metadata(args.metadata), evaluators))


if __name__ == "__main__":
    main()
