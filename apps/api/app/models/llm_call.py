from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

PURPOSE_MAX_LENGTH = 50
PROMPT_VERSION_MAX_LENGTH = 50
PROVIDER_MAX_LENGTH = 30
MODEL_MAX_LENGTH = 100


class LlmCall(Base):
    """One row per LLM request, for the monthly budget guard and the cost report.

    Holds no prompt or reply text, because both can contain comments and captions.
    """

    __tablename__ = "llm_calls"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(index=True, nullable=True)
    purpose: Mapped[str] = mapped_column(String(PURPOSE_MAX_LENGTH))
    prompt_version: Mapped[str] = mapped_column(String(PROMPT_VERSION_MAX_LENGTH))
    provider: Mapped[str] = mapped_column(String(PROVIDER_MAX_LENGTH))
    model: Mapped[str] = mapped_column(String(MODEL_MAX_LENGTH))
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
