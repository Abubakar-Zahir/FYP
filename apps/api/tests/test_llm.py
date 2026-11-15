import asyncio
import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from app.core.settings import LlmProviderName, Settings
from app.models.llm_call import LlmCall
from app.services.llm import (
    DatabaseLedger,
    InMemoryLedger,
    LlmBadResponse,
    LlmBudgetExceeded,
    LlmClient,
    LlmNotConfigured,
    LlmPrompt,
    LlmRequestRejected,
    LlmUnavailable,
    LlmUsage,
    OpenAICompatibleProvider,
    Pricing,
    build_llm_client,
    start_of_month,
)
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

PROMPT = LlmPrompt(system="Answer in JSON.", user="Classify this hook.", max_output_tokens=200)
PRICING = Pricing(input_usd_per_million=2.0, output_usd_per_million=10.0)
COMPLETION = {
    "choices": [{"message": {"role": "assistant", "content": '{"hook_type": "question"}'}}],
    "usage": {"prompt_tokens": 1000, "completion_tokens": 100},
}


def _provider(handler: Callable[[httpx.Request], httpx.Response]) -> OpenAICompatibleProvider:
    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OpenAICompatibleProvider(http, "https://llm.example/v1/", "sk-test", "test-model")


def _answer(status: int = 200, body: object = COMPLETION) -> Callable[[httpx.Request], httpx.Response]:
    return lambda _: httpx.Response(status, json=body)


def test_provider_sends_a_json_chat_request_and_reads_usage() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=COMPLETION)

    reply = asyncio.run(_provider(handler).complete(PROMPT))

    assert reply.text == '{"hook_type": "question"}'
    assert (reply.usage.input_tokens, reply.usage.output_tokens) == (1000, 100)
    request = seen[0]
    assert str(request.url) == "https://llm.example/v1/chat/completions"
    assert request.headers["Authorization"] == "Bearer sk-test"
    body = json.loads(request.content)
    assert body["model"] == "test-model"
    assert body["temperature"] == 0
    assert body["response_format"] == {"type": "json_object"}
    assert [message["role"] for message in body["messages"]] == ["system", "user"]


def test_plain_text_prompts_skip_json_mode() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=COMPLETION)

    asyncio.run(_provider(handler).complete(PROMPT.model_copy(update={"json_output": False})))

    assert "response_format" not in json.loads(seen[0].content)


@pytest.mark.parametrize("status", [429, 500, 503])
def test_rate_limits_and_server_errors_are_retryable(status: int) -> None:
    with pytest.raises(LlmUnavailable):
        asyncio.run(_provider(_answer(status, {"error": "busy"})).complete(PROMPT))


def test_network_failure_is_retryable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    with pytest.raises(LlmUnavailable):
        asyncio.run(_provider(handler).complete(PROMPT))


def test_a_rejected_request_is_not_retryable() -> None:
    with pytest.raises(LlmRequestRejected):
        asyncio.run(_provider(_answer(400, {"error": "bad model"})).complete(PROMPT))


def test_error_messages_never_include_the_api_key() -> None:
    with pytest.raises(LlmRequestRejected) as raised:
        asyncio.run(_provider(_answer(401, {"error": "bad key"})).complete(PROMPT))

    assert "sk-test" not in str(raised.value)


def test_a_reply_without_usage_is_rejected() -> None:
    body = {"choices": [{"message": {"content": "{}"}}]}

    with pytest.raises(LlmBadResponse):
        asyncio.run(_provider(_answer(body=body)).complete(PROMPT))


def test_pricing_is_per_million_tokens() -> None:
    assert PRICING.cost(LlmUsage(input_tokens=1_000_000, output_tokens=500_000)) == pytest.approx(7.0)


def test_client_records_tokens_and_cost() -> None:
    ledger = InMemoryLedger()
    client = LlmClient(_provider(_answer()), ledger, PRICING, monthly_budget_usd=30)

    text = asyncio.run(client.complete(PROMPT, purpose="dna.structure", prompt_version="v1", user_id=None))

    assert text == '{"hook_type": "question"}'
    call = ledger.calls[0]
    assert (call.purpose, call.prompt_version, call.model) == ("dna.structure", "v1", "test-model")
    assert (call.input_tokens, call.output_tokens) == (1000, 100)
    assert call.cost_usd == pytest.approx(0.003)
    assert client.model_version == "openai_compatible:test-model"


def test_client_refuses_once_the_budget_is_used_up() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json=COMPLETION)

    spent = LlmCall(
        purpose="x",
        prompt_version="v1",
        provider="p",
        model="m",
        input_tokens=0,
        output_tokens=0,
        cost_usd=30.0,
    )
    client = LlmClient(_provider(handler), InMemoryLedger([spent]), PRICING, monthly_budget_usd=30)

    with pytest.raises(LlmBudgetExceeded):
        asyncio.run(client.complete(PROMPT, purpose="dna.structure", prompt_version="v1", user_id=None))
    assert calls == []


def test_month_starts_at_midnight_utc_on_the_first() -> None:
    assert start_of_month(datetime(2026, 11, 16, 13, 5, tzinfo=UTC)) == datetime(2026, 11, 1, tzinfo=UTC)


def test_database_ledger_counts_only_this_month(factory: async_sessionmaker[AsyncSession]) -> None:
    def row(cost: float, created_at: datetime) -> LlmCall:
        return LlmCall(
            purpose="x",
            prompt_version="v1",
            provider="p",
            model="m",
            input_tokens=1,
            output_tokens=1,
            cost_usd=cost,
            created_at=created_at,
        )

    async def scenario() -> float:
        now = datetime.now(UTC)
        async with factory() as session:
            ledger = DatabaseLedger(session)
            await ledger.record(row(1.25, now))
            await ledger.record(row(5.0, start_of_month(now) - timedelta(days=1)))
            return await ledger.spent_this_month()

    assert asyncio.run(scenario()) == pytest.approx(1.25)


def test_client_needs_every_setting_including_prices() -> None:
    settings = Settings(
        llm_provider=LlmProviderName.OPENAI_COMPATIBLE,
        llm_base_url="https://llm.example/v1",
        llm_model="m",
        llm_api_key=SecretStr("sk-test"),
    )

    with pytest.raises(LlmNotConfigured):
        build_llm_client(settings, httpx.AsyncClient(), InMemoryLedger())


def test_client_builds_from_settings() -> None:
    settings = Settings(
        llm_provider=LlmProviderName.OPENAI_COMPATIBLE,
        llm_base_url="https://llm.example/v1",
        llm_model="m",
        llm_api_key=SecretStr("sk-test"),
        llm_input_usd_per_million_tokens=1,
        llm_output_usd_per_million_tokens=2,
    )

    client = build_llm_client(settings, httpx.AsyncClient(), InMemoryLedger())

    assert client.model_version == "openai_compatible:m"
