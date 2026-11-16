import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.models.dna import DnaRecordRow
from app.models.experiment import BanditBelief
from app.models.reel import CommentTheme, Reel, ReelSource
from app.services import reports
from app.workers.tasks import TaskName
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tests.support import USER_A, FakeQueue, bearer

from ml.reports.weekly import LearnerHint, ReelResult, ThemeSummary, build_report

A = bearer("token-a")
NOW = datetime.now(UTC)


async def _seed(factory: async_sessionmaker[AsyncSession]) -> None:
    async with factory() as session:
        rows = [
            # (days ago, views, reach, outlier, hook type)
            (2, 4000, 3000, 2.5, "question"),
            (5, 1000, 800, 0.6, "story"),
            (10, 2000, 1500, 1.2, "question"),
            (40, 1500, 1000, 1.0, None),  # the previous period
        ]
        for index, (days, views, reach, outlier, hook) in enumerate(rows):
            reel = Reel(
                user_id=USER_A.id,
                source=ReelSource.OWN,
                title=f"Reel {index}",
                ig_media_id=f"m{index}",
                posted_at=NOW - timedelta(days=days),
                views=views,
                reach=reach,
                saves=10,
                shares=5,
                avg_watch_time_s=8.0,
                outlier_score=outlier,
            )
            session.add(reel)
            await session.flush()
            if hook:
                session.add(
                    DnaRecordRow(
                        user_id=USER_A.id,
                        reel_id=reel.id,
                        schema_version="1.0",
                        hook_type=hook,
                        hook_text="",
                        pacing_cuts_per_10s=1,
                        length_s=20,
                        cta="",
                        transcript="",
                        record={},
                        model_version="m",
                        is_template=False,
                    )
                )
        session.add(
            CommentTheme(
                user_id=USER_A.id,
                theme="Where is this place",
                size=12,
                dominant_label="question",
                example_comment_ids=[],
                idea="Pin the exact location in a reel",
                model_version="m",
            )
        )
        session.add(BanditBelief(user_id=USER_A.id, feature="hook_style", value="question", alpha=5, beta=2))
        await session.commit()


def test_overview_compares_periods_and_ranks_formats(
    client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    asyncio.run(_seed(factory))

    body = client.get("/api/v1/analytics/overview", headers=A).json()

    assert body["period_days"] == 30
    assert body["totals"]["views"] == 7000
    assert body["change"]["views"] == round((7000 - 1500) / 1500, 4)
    assert len(body["trend"]) == 30 and sum(point["views"] for point in body["trend"]) == 7000
    assert [f["hook_type"] for f in body["best_formats"]] == ["question", "story"]
    assert body["best_formats"][0] == {"hook_type": "question", "reels": 2, "median_outlier": 1.85}


def test_overview_with_no_reels_is_all_zero(client: TestClient) -> None:
    body = client.get("/api/v1/analytics/overview", headers=A).json()

    assert body["totals"]["views"] == 0 and body["best_formats"] == [] and body["change"]["views"] == 0


def test_no_report_before_the_first_build(client: TestClient) -> None:
    response = client.get("/api/v1/reports/weekly", headers=A)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "report_not_ready"


def test_report_is_built_and_rebuilding_replaces_it(
    client: TestClient, factory: async_sessionmaker[AsyncSession]
) -> None:
    asyncio.run(_seed(factory))

    async def build() -> None:
        async with factory() as session:
            await reports.build_for_user(session, USER_A.id, NOW)
            await reports.build_for_user(session, USER_A.id, NOW)

    asyncio.run(build())
    body = client.get("/api/v1/reports/weekly", headers=A).json()

    assert body["themes"] == ["Where is this place"]
    assert body["ideas"][0]["title"] == "Pin the exact location in a reel"
    assert any("question hook" in idea["title"] for idea in body["ideas"])  # learner: 4 wins in 5 tests
    assert body["week_start"] == (reports.week_start(NOW.date()) - timedelta(days=7)).isoformat()


def test_report_endpoint_queues_a_job(client: TestClient, queue: FakeQueue) -> None:
    response = client.post("/api/v1/reports/weekly", headers=A)

    assert response.status_code == 202
    assert queue.sent == [(TaskName.REPORTS_WEEKLY, UUID(response.json()["job_id"]))]


def test_report_wins_and_losses_follow_the_usual_views() -> None:
    report = build_report(
        "2026-11-09",
        [
            ReelResult("Hit", "question", 9000, 3.0),
            ReelResult("Miss", "story", 300, 0.4),
            ReelResult("New", None, None, None),
        ],
        [ThemeSummary("Price", "Show the price list", 7)],
        [LearnerHint("opener", "face", 0.4, 5)],
    )

    assert report.headline == "3 reels this week. The best did 3.0x your usual views."
    assert [item.title for item in report.wins] == ["Hit"]
    assert [item.title for item in report.losses] == ["Miss"]
    assert [idea.title for idea in report.ideas] == ["Show the price list"]  # a 40% hint isn't advice


def test_an_empty_week_says_so() -> None:
    assert build_report("2026-11-09", [], [], []).headline.startswith("No new reels this week")
