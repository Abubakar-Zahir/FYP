import asyncio
import json

from ml.comments.ideas import ThemeInput, fallback_idea, name_themes
from ml.comments.labels import CommentLabel
from ml.comments.themes import find_themes

LOCATION = [f"Ye jagah kahan hai bhai {n}" for n in range(20)] + [
    f"location kahan hai please {n}" for n in range(10)
]
PRICE = [f"price bohat mehnga hai yaar {n}" for n in range(20)] + [
    f"itna mehnga price kyun {n}" for n in range(10)
]
SPAM = [f"follow back karo {n}" for n in range(15)]


def _labels(count: int, label: CommentLabel) -> list[CommentLabel]:
    return [label] * count


def test_themes_separate_location_questions_from_price_complaints() -> None:
    texts = LOCATION + PRICE + SPAM
    labels = (
        _labels(30, CommentLabel.QUESTION)
        + _labels(30, CommentLabel.COMPLAINT)
        + _labels(15, CommentLabel.SPAM)
    )

    themes = find_themes(texts, labels, max_themes=2)

    assert len(themes) == 2
    by_label = {theme.dominant_label: theme for theme in themes}
    assert "kahan" in " ".join(by_label[CommentLabel.QUESTION].terms)
    assert "mehnga" in " ".join(by_label[CommentLabel.COMPLAINT].terms)
    assert all(index < 60 for theme in themes for index in theme.members)  # spam is left out
    assert themes[0].size >= themes[1].size


def test_too_few_comments_give_no_themes() -> None:
    assert find_themes(LOCATION[:10], _labels(10, CommentLabel.QUESTION)) == []


def test_themes_are_stable_across_runs() -> None:
    texts = LOCATION + PRICE
    labels = _labels(60, CommentLabel.QUESTION)

    assert find_themes(texts, labels, max_themes=2) == find_themes(texts, labels, max_themes=2)


def test_fallback_ideas_never_invent_content() -> None:
    question = ThemeInput(
        terms=["kahan", "jagah"], dominant_label=CommentLabel.QUESTION, examples=["Ye kahan hai?"]
    )
    praise = ThemeInput(terms=["zabardast", "taste"], dominant_label=CommentLabel.PRAISE, examples=[])

    assert fallback_idea(question).idea == 'Make a reel that answers: "Ye kahan hai?"'
    assert "zabardast / taste" in fallback_idea(praise).idea


def test_llm_names_themes_and_bad_answers_fall_back() -> None:
    theme = ThemeInput(terms=["kahan"], dominant_label=CommentLabel.QUESTION, examples=["Ye kahan hai?"])

    async def good(system: str, user: str) -> str:
        return json.dumps(
            {"themes": [{"id": 0, "name": "Where is this place", "idea": "Pin the exact location."}]}
        )

    async def bad(system: str, user: str) -> str:
        return "nope"

    [named] = asyncio.run(name_themes("food", [theme], good))
    [fallback] = asyncio.run(name_themes("food", [theme], bad))
    [no_llm] = asyncio.run(name_themes("food", [theme], None))

    assert (named.name, named.idea) == ("Where is this place", "Pin the exact location.")
    assert fallback == no_llm == fallback_idea(theme)
