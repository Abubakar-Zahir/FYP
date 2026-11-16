import json
import random
from pathlib import Path

import pytest

from ml.dna.schema import HookType
from ml.scoring.evaluate import cross_validate, full_report, hook_type_baseline
from ml.scoring.features import READABLE_NAMES, feature_matrix, readable_features
from ml.scoring.model import HookExample, HookScorer, target
from ml.scoring.train import read_examples

QUESTIONS = [
    "Lahore ki sab se sasti biryani kahan hai?",
    "Kya ye 300 ka burger worth it hai?",
    "Where is the best chai?",
]
STATEMENTS = [
    "Today I went to a cafe and then I came home later",
    "Main ne aaj kuch khaya aur phir ghar gaya",
    "Vlog day 12",
]


def _synthetic(creators: int = 6, per_creator: int = 20) -> list[HookExample]:
    """Questions do about 3x better than statements, plus noise, for every creator."""
    generator = random.Random(1)
    examples = []
    for creator in range(creators):
        for n in range(per_creator):
            is_question = n % 2 == 0
            text = (QUESTIONS if is_question else STATEMENTS)[n % 3] + f" {n}"
            base = 3.0 if is_question else 1.0
            examples.append(
                HookExample(
                    text=text,
                    hook_type=HookType.QUESTION if is_question else HookType.STORY,
                    creator=f"c{creator}",
                    outlier_score=base * generator.uniform(0.7, 1.3),
                )
            )
    return examples


def test_readable_features_have_one_value_per_name() -> None:
    values = readable_features("Kya ye Rs 300 ka hai? 😍", HookType.QUESTION)

    named = dict(zip(READABLE_NAMES, values, strict=True))
    assert named["has_question"] == 1.0
    assert named["starts_with_question_word"] == 1.0
    assert named["has_price"] == 1.0
    assert named["emoji_count"] == 1.0
    assert named["hook_type_question"] == 1.0
    assert named["roman_urdu_share"] > 0


def test_feature_matrix_shapes() -> None:
    assert feature_matrix(["a", "b"], [None, None], with_wording=False).shape == (2, len(READABLE_NAMES))
    assert feature_matrix(["a", "b"], [None, None], with_wording=True).shape == (2, len(READABLE_NAMES) + 64)


def test_the_scorer_learns_that_questions_win_and_explains_why(tmp_path: Path) -> None:
    model = HookScorer.train(_synthetic())
    model.save(tmp_path)
    loaded = HookScorer.load(tmp_path)

    question, statement = loaded.score(
        ["Kahan milti hai sab se achhi chaat?", "I went home after work today"],
        [HookType.QUESTION, HookType.STORY],
    )

    assert question.score > statement.score
    assert 0 <= statement.score <= question.score <= 100
    assert 1 <= len(question.top_factors) <= 3
    assert loaded.version == model.version == "lgbm-wording-v1"


def test_training_is_deterministic() -> None:
    first = HookScorer.train(_synthetic()).predict_log_outlier(["Kya scene hai?"], [HookType.QUESTION])
    second = HookScorer.train(_synthetic()).predict_log_outlier(["Kya scene hai?"], [HookType.QUESTION])

    assert first == second


def test_creator_split_cross_validation_finds_the_signal() -> None:
    reports = full_report(_synthetic())

    by_name = {report.model: report for report in reports}
    assert by_name["lgbm: readable + wording"].spearman > 0.5
    assert by_name["lgbm: readable + wording"].creators == 6
    for report in reports:
        assert report.spearman_low <= report.spearman <= report.spearman_high


def test_cross_validation_needs_two_creators() -> None:
    one_creator = [example for example in _synthetic() if example.creator == "c0"]

    with pytest.raises(ValueError, match="two creators"):
        cross_validate("x", one_creator, hook_type_baseline)


def test_target_rejects_non_positive_scores() -> None:
    assert target(1.0) == 0.0
    with pytest.raises(ValueError):
        target(0.0)


def test_jsonl_dataset_is_read(tmp_path: Path) -> None:
    path = tmp_path / "hooks.jsonl"
    path.write_text(
        json.dumps({"text": "Kya?", "hook_type": "question", "creator": "a", "outlier_score": 2.0})
        + "\n\n"
        + json.dumps({"text": "Hi", "hook_type": None, "creator": "b", "outlier_score": 0.5})
        + "\n",
        encoding="utf-8",
    )

    examples = read_examples(path)

    assert [(e.hook_type, e.creator) for e in examples] == [(HookType.QUESTION, "a"), (None, "b")]
