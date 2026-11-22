"""Exports hooks with their per-account outlier score, for ml.scoring.train.

    PYTHONPATH=apps/api:. uv run python apps/api/scripts/export_hook_dataset.py data/hooks.jsonl

One line per own reel that has a DNA record (hook text and type) and an outlier score. Creator
ids are hashed, so the file names no account. It still holds hook text, so keep it in data/.
"""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from app.core.settings import get_settings
from app.models.dna import DnaRecordRow
from app.models.reel import Reel, ReelSource
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

CREATOR_HASH_LENGTH = 12


def creator_key(user_id: object) -> str:
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:CREATOR_HASH_LENGTH]


async def export(out: Path) -> int:
    database_url = get_settings().database_url
    if not database_url:
        raise SystemExit("Set DATABASE_URL first")
    engine = create_async_engine(database_url, hide_parameters=True)
    query = (
        select(DnaRecordRow.hook_text, DnaRecordRow.hook_type, Reel.user_id, Reel.outlier_score)
        .join(Reel, Reel.id == DnaRecordRow.reel_id)
        .where(Reel.source == ReelSource.OWN, Reel.outlier_score.is_not(None), Reel.outlier_score > 0)
    )
    async with engine.connect() as connection:
        rows = (await connection.execute(query)).all()
    await engine.dispose()
    lines = [
        json.dumps({"text": text, "hook_type": kind, "creator": creator_key(user), "outlier_score": score})
        for text, kind, user, score in rows
        if text.strip()
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return len(lines)


def main() -> None:
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("out", type=Path)
    args = arguments.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    print(f"Wrote {asyncio.run(export(args.out))} hooks to {args.out}")


if __name__ == "__main__":
    main()
