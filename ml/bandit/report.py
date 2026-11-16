"""Writes the simulator's regret curves for the evaluation report.

    uv run python -m ml.bandit.report --rounds 20 60 --out data/reports/bandit_regret.json

Report the curves as they come out. In the version 1 run, Thompson sampling and epsilon-greedy
were close, and both far below random. The pilot decides which policy ships.
"""

import argparse
import json
from pathlib import Path

from ml.bandit.simulator import compare


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("--rounds", type=int, nargs="+", default=[20, 60])
    arguments.add_argument("--creators", type=int, default=50)
    arguments.add_argument("--per-round", type=int, default=3)
    arguments.add_argument("--out", type=Path, default=Path("data/reports/bandit_regret.json"))
    args = arguments.parse_args()
    results = {}
    for rounds in args.rounds:
        curves = compare(creators=args.creators, rounds=rounds, per_round=args.per_round)
        results[str(rounds)] = [curve.model_dump() for curve in curves]
        print(f"{rounds} rounds: " + ", ".join(f"{c.policy} {c.final}" for c in curves))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
