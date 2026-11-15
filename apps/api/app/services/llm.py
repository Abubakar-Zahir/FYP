"""The only way the platform calls an LLM (docs/backend.md, ML integration).

Every call checks the monthly budget first and records tokens and cost after, so pilot
spend stays under LLM_MONTHLY_BUDGET_USD (CLAUDE.md hard constraint 4). The provider is
chosen by LLM_PROVIDER, so swapping it is a configuration change.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

import httpx
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import LlmProviderName, Settings
from app.models.llm_call import LlmCall

TOKENS_PER_MILLION = 1_000_000
LLM_TIMEOUT_SECONDS = 60.0
RETRYABLE_STATUS_CODES = frozenset({408, 409, 429, 500, 502, 503, 504})


class LlmError(Exception):
    """Base class. Messages never include the prompt, the reply or the API key."""


class LlmNotConfigured(LlmError):
    pass


class LlmBudgetExceeded(LlmError):
    pass


class LlmUnavailable(LlmError):
    """Timeouts, rate limits and server errors. Worth retrying later."""


class LlmRequestRejected(LlmError):
    """The provider refused the request itself. Retrying the same request won't help."""


class LlmBadResponse(LlmError):
    pass


class LlmPrompt(BaseModel):
    system: str
    user: str
    max_output_tokens: int = Field(gt=0)
    json_output: bool = True


class LlmUsage(BaseModel):
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0)


class LlmReply(BaseModel):
    text: str
    usage: LlmUsage


class LlmProvider(Protocol):
    name: str
    model: str

    async def complete(self, prompt: LlmPrompt) -> LlmReply: ...


class OpenAICompatibleProvider:
    """Chat Completions over HTTP. Works with OpenRouter and Gemini's OpenAI-compatible endpoint."""

    name = LlmProviderName.OPENAI_COMPATIBLE.value

    def __init__(self, http: httpx.AsyncClient, base_url: str, api_key: str, model: str) -> None:
        self._http = http
        self._url = f"{base_url.rstrip('/')}/chat/completions"
        self._api_key = api_key
        self.model = model

    def _body(self, prompt: LlmPrompt) -> dict[str, object]:
        body: dict[str, object] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": prompt.user},
            ],
            "max_tokens": prompt.max_output_tokens,
            "temperature": 0,
        }
        if prompt.json_output:
            body["response_format"] = {"type": "json_object"}
        return body

    async def complete(self, prompt: LlmPrompt) -> LlmReply:
        try:
            response = await self._http.post(
                self._url,
                json=self._body(prompt),
                headers={"Authorization": f"Bearer {self._api_key}"},
                timeout=LLM_TIMEOUT_SECONDS,
            )
        except httpx.TransportError as error:
            raise LlmUnavailable("The LLM provider could not be reached") from error
        if response.status_code in RETRYABLE_STATUS_CODES:
            raise LlmUnavailable(f"The LLM provider answered {response.status_code}")
        if response.is_error:
            raise LlmRequestRejected(f"The LLM provider rejected the request with {response.status_code}")
        return _parse_chat_completion(response)


def _parse_chat_completion(response: httpx.Response) -> LlmReply:
    try:
        body = response.json()
        text = body["choices"][0]["message"]["content"]
        usage = body["usage"]
        return LlmReply(
            text=text,
            usage=LlmUsage(input_tokens=usage["prompt_tokens"], output_tokens=usage["completion_tokens"]),
        )
    except (ValueError, KeyError, IndexError, TypeError) as error:
        # Without usage the cost is unknown, and the budget guard can't work.
        raise LlmBadResponse("The LLM reply was missing its text or token usage") from error


@dataclass(frozen=True)
class Pricing:
    input_usd_per_million: float
    output_usd_per_million: float

    def cost(self, usage: LlmUsage) -> float:
        return (
            usage.input_tokens * self.input_usd_per_million
            + usage.output_tokens * self.output_usd_per_million
        ) / TOKENS_PER_MILLION


class Ledger(Protocol):
    async def spent_this_month(self) -> float: ...

    async def record(self, call: LlmCall) -> None: ...


def start_of_month(now: datetime) -> datetime:
    return now.astimezone(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)


class DatabaseLedger:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def spent_this_month(self) -> float:
        since = start_of_month(datetime.now(UTC))
        query = select(func.coalesce(func.sum(LlmCall.cost_usd), 0.0)).where(LlmCall.created_at >= since)
        return float((await self._session.execute(query)).scalar_one())

    async def record(self, call: LlmCall) -> None:
        self._session.add(call)
        await self._session.commit()


@dataclass
class InMemoryLedger:
    """For spikes and tests, where there is no database."""

    calls: list[LlmCall] = field(default_factory=list)

    async def spent_this_month(self) -> float:
        return sum(call.cost_usd for call in self.calls)

    async def record(self, call: LlmCall) -> None:
        self.calls.append(call)


class LlmClient:
    def __init__(
        self, provider: LlmProvider, ledger: Ledger, pricing: Pricing, monthly_budget_usd: float
    ) -> None:
        self._provider = provider
        self._ledger = ledger
        self._pricing = pricing
        self._budget = monthly_budget_usd

    @property
    def model_version(self) -> str:
        return f"{self._provider.name}:{self._provider.model}"

    async def complete(
        self, prompt: LlmPrompt, *, purpose: str, prompt_version: str, user_id: UUID | None
    ) -> str:
        # Checked before the call, so one call can overshoot by its own cost, never more.
        if await self._ledger.spent_this_month() >= self._budget:
            raise LlmBudgetExceeded("The monthly LLM budget is used up")
        reply = await self._provider.complete(prompt)
        await self._ledger.record(
            LlmCall(
                user_id=user_id,
                purpose=purpose,
                prompt_version=prompt_version,
                provider=self._provider.name,
                model=self._provider.model,
                input_tokens=reply.usage.input_tokens,
                output_tokens=reply.usage.output_tokens,
                cost_usd=self._pricing.cost(reply.usage),
            )
        )
        return reply.text


def build_llm_client(settings: Settings, http: httpx.AsyncClient, ledger: Ledger) -> LlmClient:
    """Refuses to start without prices, because the budget guard needs them."""
    base_url = settings.llm_base_url
    model = settings.llm_model
    api_key = settings.llm_api_key
    input_price = settings.llm_input_usd_per_million_tokens
    output_price = settings.llm_output_usd_per_million_tokens
    if (
        settings.llm_provider is None
        or base_url is None
        or model is None
        or api_key is None
        or input_price is None
        or output_price is None
    ):
        raise LlmNotConfigured(
            "Set LLM_PROVIDER, LLM_BASE_URL, LLM_MODEL, LLM_API_KEY, "
            "LLM_INPUT_USD_PER_MILLION_TOKENS and LLM_OUTPUT_USD_PER_MILLION_TOKENS"
        )
    provider = OpenAICompatibleProvider(http, base_url, api_key.get_secret_value(), model)
    return LlmClient(provider, ledger, Pricing(input_price, output_price), settings.llm_monthly_budget_usd)
