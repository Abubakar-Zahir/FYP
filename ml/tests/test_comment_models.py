import asyncio
import json
from pathlib import Path
from typing import Any

import pytest

from ml.comments.dataset import LabelledComment, from_label_studio, split_by_group
from ml.comments.evaluate import evaluate
from ml.comments.labels import CommentLabel
from ml.comments.models import CharNgramClassifier, EnglishOnlyBaseline, load_sklearn_classifier
from ml.comments.normalise import normalise
from ml.comments.train import train_and_report
from ml.comments.zero_shot import classify, parse_labels

# Small synthetic set: a few clear examples per label, in English and Roman Urdu.
EXAMPLES: dict[CommentLabel, list[tuple[str, str]]] = {
    CommentLabel.QUESTION: [
        ("Ye kahan hai?", "roman_urdu"),
        ("Where is this place?", "english"),
        ("Kitne ka hai ye?", "roman_urdu"),
        ("What is the price?", "english"),
    ],
    CommentLabel.REQUEST: [
        ("Karachi ka bhi review karo", "roman_urdu"),
        ("Please review Karachi too", "english"),
        ("Part 2 banao please", "roman_urdu"),
        ("Make a video on biryani", "english"),
    ],
    CommentLabel.PRAISE: [
        ("Bohat acha content", "roman_urdu"),
        ("Love this video", "english"),
        ("Zabardast bhai", "roman_urdu"),
        ("Amazing work", "english"),
    ],
    CommentLabel.OBJECTION: [
        ("150 nahi 200 ka hai ab", "roman_urdu"),
        ("It costs 200 now, not 150", "english"),
        ("Ye galat hai, wahan nahi hai", "roman_urdu"),
        ("That is wrong, it closed", "english"),
    ],
    CommentLabel.COMPLAINT: [
        ("Awaz bohat kharab hai", "roman_urdu"),
        ("The sound is terrible", "english"),
        ("Bohat mehnga hai yaar", "roman_urdu"),
        ("Too expensive and dirty", "english"),
    ],
    CommentLabel.SPAM: [
        ("Follow back karo", "roman_urdu"),
        ("Earn 500 daily DM me", "english"),
        ("First!", "english"),
        ("Check my page", "english"),
    ],
}


def _items() -> list[LabelledComment]:
    return [
        LabelledComment(id=f"{label.value}-{n}", text=text, label=label, language=language, group=f"reel-{n}")
        for label, examples in EXAMPLES.items()
        for n, (text, language) in enumerate(examples)
    ]


def _task(
    task_id: int,
    text: str,
    label: str,
    reel: str = "r1",
    cancelled: bool = False,
    language: str = "roman_urdu",
) -> dict[str, Any]:
    return {
        "id": task_id,
        "data": {"text": text, "reel_id": reel},
        "annotations": [
            {
                "was_cancelled": cancelled,
                "result": [
                    {"from_name": "label", "value": {"choices": [label]}},
                    {"from_name": "language", "value": {"choices": [language]}},
                ],
            }
        ],
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Kia BAAAT hai!!!!", "kya baat hai ! !"),
        ("yeh bht acha h", "ye bohot achha hai"),
        ("@ali dekh yaar https://x.co/abc", "usertag dekh yaar urltag"),
        ("he told me", "he told me"),
        ("بہت زبردست", "بہت زبردست"),
    ],
)
def test_normalise(raw: str, expected: str) -> None:
    assert normalise(raw) == expected


def test_label_studio_export_is_read_and_bad_tasks_skipped() -> None:
    tasks = [
        _task(1, "Ye kahan hai?", "question", reel="r9"),
        _task(2, "nope", "not-a-label"),
        _task(3, "cancelled", "praise", cancelled=True),
        {"id": 4, "data": {"text": "no annotations"}, "annotations": []},
    ]

    [item] = from_label_studio(tasks)

    assert (item.id, item.label, item.group, item.language) == (
        "1",
        CommentLabel.QUESTION,
        "r9",
        "roman_urdu",
    )


def test_split_keeps_each_reel_on_one_side_and_is_stable() -> None:
    items = [
        LabelledComment(id=str(n), text="x", label=CommentLabel.PRAISE, language=None, group=f"reel-{n % 40}")
        for n in range(400)
    ]

    train, test = split_by_group(items)

    assert {item.group for item in train}.isdisjoint({item.group for item in test})
    assert 0.05 < len(test) / len(items) < 0.4
    assert split_by_group(items) == (train, test)


def test_char_model_learns_the_synthetic_set_and_round_trips(tmp_path: Path) -> None:
    model = CharNgramClassifier().fit(_items())
    model.save(tmp_path / "m.joblib")
    loaded = load_sklearn_classifier(tmp_path / "m.joblib")

    texts = ["Ye kahan hai?", "Awaz bohat kharab hai"]
    assert model.predict(texts) == [CommentLabel.QUESTION, CommentLabel.COMPLAINT]
    assert loaded.predict(texts) == model.predict(texts)
    assert loaded.name == "char-ngram-logreg-v1"


def test_english_baseline_trains_on_english_only() -> None:
    model = EnglishOnlyBaseline().fit(_items())

    assert model.predict(["The sound is terrible"]) == [CommentLabel.COMPLAINT]


def test_training_needs_two_labels() -> None:
    one_label = [item for item in _items() if item.label == CommentLabel.PRAISE]

    with pytest.raises(ValueError, match="two different labels"):
        CharNgramClassifier().fit(one_label)


def test_evaluation_reports_macro_f1_with_an_interval() -> None:
    truth = ["praise", "praise", "question", "spam", "complaint", "praise"]
    predicted = ["praise", "question", "question", "spam", "praise", "praise"]

    report = evaluate("m", truth, predicted)

    assert 0 <= report.macro_f1_low <= report.macro_f1 <= report.macro_f1_high <= 1
    assert report.test_size == 6
    assert sum(map(sum, report.confusion)) == 6
    assert report.f1_by_label["spam"] == 1.0


def test_evaluation_rejects_mismatched_lists() -> None:
    with pytest.raises(ValueError):
        evaluate("m", ["praise"], [])


def test_train_cli_writes_model_and_report(tmp_path: Path) -> None:
    tasks = [
        _task(
            index,
            item.text,
            item.label.value,
            reel=f"{item.group}-{item.label.value}-{index}",
            language=str(item.language),
        )
        for index, item in enumerate(_items() * 3)
    ]

    reports = train_and_report(tasks, tmp_path)

    assert [report.model for report in reports] == ["char-ngram-logreg-v1", "english-only-word-logreg-v1"]
    assert (tmp_path / "char_ngram.joblib").exists()
    assert json.loads((tmp_path / "report.json").read_text())["test_size"] > 0


def test_zero_shot_parses_answers_and_marks_missing_ones() -> None:
    raw = json.dumps(
        {"labels": [{"id": 0, "label": "question"}, {"id": 2, "label": "spam"}, {"id": 9, "label": "praise"}]}
    )

    assert parse_labels(raw, 3) == [CommentLabel.QUESTION, None, CommentLabel.SPAM]


def test_zero_shot_batches_and_survives_a_bad_batch() -> None:
    calls: list[str] = []

    async def llm(system: str, user: str) -> str:
        calls.append(user)
        if len(calls) == 2:
            return "not json"
        count = user.count("\n")
        return json.dumps({"labels": [{"id": n, "label": "praise"} for n in range(count)]})

    labels = asyncio.run(classify(["Nice"] * 30, llm))

    assert len(calls) == 2
    assert labels[:25] == [CommentLabel.PRAISE] * 25
    assert labels[25:] == [None] * 5
