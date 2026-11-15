from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

IG_USER_ID_MAX_LENGTH = 64
USERNAME_MAX_LENGTH = 64
ACCOUNT_TYPE_MAX_LENGTH = 32


class InstagramAccount(Base):
    """One connected Instagram account per user (docs/backend.md, `ig_accounts`).

    `user_id` has no foreign key to `users`, because a creator can connect Instagram
    before the onboarding profile row exists. Deleting a user removes this row explicitly.
    """

    __tablename__ = "ig_accounts"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(unique=True, index=True)
    ig_user_id: Mapped[str] = mapped_column(String(IG_USER_ID_MAX_LENGTH))
    username: Mapped[str] = mapped_column(String(USERNAME_MAX_LENGTH))
    account_type: Mapped[str] = mapped_column(String(ACCOUNT_TYPE_MAX_LENGTH))
    # Fernet ciphertext (rules.md 6.2). The plain token never reaches the database.
    encrypted_token: Mapped[str] = mapped_column(Text)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
