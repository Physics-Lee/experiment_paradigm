"""Stable CSV and JSON result persistence."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def write_csv(path: Path, trials: list[dict[str, Any]]) -> None:
    """Write trial rows using the first row's stable field order."""
    if not trials:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(trials[0].keys()))
        writer.writeheader()
        writer.writerows(trials)


def write_json(
    path: Path,
    *,
    experiment_start: str,
    trials: list[dict[str, Any]],
) -> None:
    """Write the paired structured result file."""
    payload = {
        "experiment_start": experiment_start,
        "total_trials": len(trials),
        "trials": trials,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def write_run_results(
    *,
    trials: list[dict[str, Any]],
    output_prefix: str,
    experiment_start: str,
    output_dir: Path = Path("timestamp"),
) -> tuple[Path, Path] | None:
    """Write paired timestamped CSV/JSON results and return their paths."""
    if not trials:
        print("No data to save.")
        return None
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = output_dir / f"{output_prefix}_{timestamp}.csv"
    json_path = output_dir / f"{output_prefix}_{timestamp}.json"
    write_csv(csv_path, trials)
    write_json(
        json_path,
        experiment_start=experiment_start,
        trials=trials,
    )
    return csv_path, json_path
