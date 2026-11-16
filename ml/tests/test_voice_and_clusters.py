from ml.dna.clusters import MIN_RECORDS, cluster_formats
from ml.dna.schema import Beat, DnaRecord, HookType, ReelSignals
from ml.scripts.voice import pick_samples

CAPTIONS = [
    "Gym ka pehla din, legs dead",
    "Lahore ki sab se crispy samosa chaat Anarkali mein",
    "Biryani review: Karachi vs Lahore",
    "",
    "Sunday vlog with family",
]


def _record(hook: HookType, pacing: float, length: float) -> DnaRecord:
    return DnaRecord(
        signals=ReelSignals(
            length_s=length,
            cut_times_s=[],
            pacing_cuts_per_10s=pacing,
            detected_language="ur",
            transcript=[],
            hook_candidate_text="",
            keyframe_paths=[],
            model_version="w",
        ),
        hook_type=hook,
        hook_text="",
        beats=[Beat(label="Hook", start_s=0, end_s=2, description="x")],
        overlays=[],
        cta="Follow",
        model_version="m",
    )


def test_voice_samples_closest_to_the_topic_come_first() -> None:
    picked = pick_samples("best chaat in Lahore", CAPTIONS, limit=2)

    assert picked[0] == "Lahore ki sab se crispy samosa chaat Anarkali mein"
    assert len(picked) == 2


def test_with_nothing_similar_the_newest_samples_are_used() -> None:
    assert pick_samples("", CAPTIONS, limit=2) == [
        "Gym ka pehla din, legs dead",
        "Lahore ki sab se crispy samosa chaat Anarkali mein",
    ]


def test_no_samples_gives_none() -> None:
    assert pick_samples("topic", ["", "  "]) == []


def test_formats_split_by_hook_and_pacing() -> None:
    fast_questions = [_record(HookType.QUESTION, 3.0, 20) for _ in range(4)]
    slow_stories = [_record(HookType.STORY, 0.5, 60) for _ in range(4)]
    outliers = [2.0, 3.0, 2.5, None, 0.8, 1.0, 0.9, None]

    clusters = cluster_formats(fast_questions + slow_stories, outliers)

    by_hook = {cluster.hook_type: cluster for cluster in clusters}
    assert sorted(by_hook[HookType.QUESTION].members) == [0, 1, 2, 3]
    assert by_hook[HookType.QUESTION].median_outlier == 2.5
    assert by_hook[HookType.QUESTION].label == "Question hook, fast cuts, ~20 s"
    assert by_hook[HookType.STORY].label == "Story hook, slow cuts, ~60 s"


def test_too_few_records_give_no_clusters() -> None:
    records = [_record(HookType.LIST, 1.0, 30)] * (MIN_RECORDS - 1)

    assert cluster_formats(records, [None] * len(records)) == []
