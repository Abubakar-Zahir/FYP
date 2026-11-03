import ast
from collections.abc import Iterator
from pathlib import Path

import pytest

ML_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = {"fastapi", "celery", "sqlalchemy", "app", "apps"}


def imported_top_level_modules(source: str) -> Iterator[str]:
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            yield from (alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".")[0]


@pytest.mark.parametrize("path", list(ML_ROOT.rglob("*.py")), ids=str)
def test_ml_stays_framework_free(path: Path) -> None:
    """rules.md 3.9: workers call into ml/, never the other way round."""
    assert not FORBIDDEN & set(imported_top_level_modules(path.read_text()))


def test_detects_forbidden_import() -> None:
    assert "fastapi" in set(imported_top_level_modules("from fastapi import APIRouter"))
