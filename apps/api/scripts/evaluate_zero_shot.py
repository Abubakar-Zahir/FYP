"""Scores the LLM zero-shot comment baseline on the same held-out split as ml.comments.train.

    PYTHONPATH=apps/api:. uv run python apps/api/scripts/evaluate_zero_shot.py data/labels/comments.json

Calls the configured LLM through the budget guard (LLM_* settings) and prints the cost. The
comments go to the provider, so use only comments your consent forms cover.
"""

import argparse
import asyncio
import json
from pathlib import Path

import httpx
from app.core.settings import get_settings
from app.services.llm import InMemoryLedger, LlmPrompt, build_llm_client

from ml.comments.dataset import from_label_studio, split_by_group
from ml.comments.evaluate import evaluate
from ml.comments.zero_shot import MAX_OUTPUT_TOKENS, PROMPT_VERSION, classify

MISSING = "missing"


async def run(export: Path, out: Path) -> None:
    _, test = split_by_group(from_label_studio(json.loads(export.read_text(encoding="utf-8"))))
    ledger = InMemoryLedger()
    async with httpx.AsyncClient() as http:
        client = build_llm_client(get_settings(), http, ledger)

        async def call(system: str, user: str) -> str:
            prompt = LlmPrompt(system=system, user=user, max_output_tokens=MAX_OUTPUT_TOKENS)
            return await client.complete(
                prompt, purpose="comments.zero_shot.eval", prompt_version=PROMPT_VERSION, user_id=None
            )

        labels = await classify([item.text for item in test], call)
    predicted = [label.value if label else MISSING for label in labels]
    report = evaluate(f"zero-shot:{client.model_version}", [item.label.value for item in test], predicted)
    out.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    cost = await ledger.spent_this_month()
    print(f"{report.model}: macro F1 {report.macro_f1} ({report.macro_f1_low} to {report.macro_f1_high})")
    print(f"{predicted.count(MISSING)} comments got no label. LLM cost USD {cost:.4f}")


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("export", type=Path)
    arguments.add_argument("--out", type=Path, default=Path("data/models/comments/zero_shot_report.json"))
    args = arguments.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(run(args.export, args.out))


if __name__ == "__main__":
    main()
