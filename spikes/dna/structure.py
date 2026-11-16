"""Turns the ReelSignals JSON from extract.py into DnaRecord JSON with the configured LLM.

Run from the repo root after extract.py, with the LLM_* settings in .env:

    PYTHONPATH=.:apps/api uv run python spikes/dna/structure.py data/dna_spike

This calls a paid API. It prints the total cost and stops at LLM_MONTHLY_BUDGET_USD.
"""

import argparse
import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path

import httpx
from app.core.settings import get_settings
from app.services.llm import InMemoryLedger, LlmClient, LlmPrompt, build_llm_client

from ml.dna.schema import ReelSignals
from ml.dna.structure import MAX_OUTPUT_TOKENS, PROMPT_VERSION, StructuringError, StructuringPrompt, structure

RECORD_SUFFIX = ".dna.json"
SKIPPED_FILES = {"timings.json"}


def caller(client: LlmClient) -> Callable[[StructuringPrompt], Awaitable[str]]:
    async def call(prompt: StructuringPrompt) -> str:
        return await client.complete(
            LlmPrompt(system=prompt.system, user=prompt.user, max_output_tokens=MAX_OUTPUT_TOKENS),
            purpose="dna.structure.spike",
            prompt_version=PROMPT_VERSION,
            user_id=None,
        )

    return call


def signal_files(folder: Path) -> list[Path]:
    return sorted(
        path
        for path in folder.glob("*.json")
        if path.name not in SKIPPED_FILES and not path.name.endswith(RECORD_SUFFIX)
    )


async def run(folder: Path) -> None:
    ledger = InMemoryLedger()
    async with httpx.AsyncClient() as http:
        client = build_llm_client(get_settings(), http, ledger)
        call = caller(client)
        for path in signal_files(folder):
            signals = ReelSignals.model_validate_json(path.read_text(encoding="utf-8"))
            try:
                record = await structure(signals, call, client.model_version)
            except StructuringError as error:
                print(f"{path.name}: failed after one retry: {error}")
                continue
            path.with_name(path.stem + RECORD_SUFFIX).write_text(
                record.model_dump_json(indent=2), encoding="utf-8"
            )
            print(f"{path.name}: {record.hook_type.value}, {len(record.beats)} beats")
    total = await ledger.spent_this_month()
    print(f"{len(ledger.calls)} LLM calls, USD {total:.4f} in total")


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("folder", type=Path, help="the --output folder of extract.py")
    asyncio.run(run(arguments.parse_args().folder))


if __name__ == "__main__":
    main()
