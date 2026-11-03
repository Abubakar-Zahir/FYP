"""Verifies Supabase access tokens against the project's public keys.

Supabase recommends against verifying locally with the shared secret, so only asymmetric
keys are accepted: https://supabase.com/docs/guides/auth/jwts
"""

import time
from collections.abc import Callable
from typing import Annotated, Any
from uuid import UUID

import httpx
import jwt
from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.core.errors import ApiError

ALLOWED_ALGORITHMS = ("ES256", "RS256")
USER_AUDIENCE = "authenticated"
REQUIRED_CLAIMS = ["exp", "iat", "sub", "aud", "iss"]
JWKS_PATH = "/.well-known/jwks.json"
JWKS_TIMEOUT_SECONDS = 5.0

# Supabase caches this endpoint for 10 minutes and asks apps not to cache it for longer.
JWKS_MAX_AGE_SECONDS = 600.0
# Tokens with made-up key ids must not be able to make us hammer Supabase.
JWKS_MIN_REFRESH_INTERVAL_SECONDS = 30.0


class CurrentUser(BaseModel):
    id: UUID
    email: str | None
    name: str | None


def _invalid_token() -> ApiError:
    # One message for every cause, so a failed token teaches an attacker nothing.
    return ApiError(status.HTTP_401_UNAUTHORIZED, "invalid_token", "The access token is not valid.")


class TokenVerifier:
    def __init__(
        self,
        issuer: str,
        http: httpx.AsyncClient,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._issuer = issuer
        self._http = http
        self._clock = clock
        self._keys: dict[str, jwt.PyJWK] = {}
        self._fetched_at: float | None = None

    async def _fetch_keys(self) -> None:
        try:
            response = await self._http.get(f"{self._issuer}{JWKS_PATH}", timeout=JWKS_TIMEOUT_SECONDS)
            response.raise_for_status()
            body = response.json()
            # An empty list is a valid answer: all keys revoked, or a project without asymmetric keys.
            keys = jwt.PyJWKSet.from_dict(body).keys if body.get("keys") else []
        except (httpx.HTTPError, ValueError, AttributeError, jwt.PyJWTError) as error:
            raise ApiError(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "auth_unavailable",
                "Sign-in could not be checked. Try again shortly.",
            ) from error
        self._keys = {key.key_id: key for key in keys if key.key_id}
        self._fetched_at = self._clock()

    async def _key_for(self, key_id: str) -> jwt.PyJWK:
        age = None if self._fetched_at is None else self._clock() - self._fetched_at
        expired = age is None or age >= JWKS_MAX_AGE_SECONDS
        unknown_key_may_be_new = (
            key_id not in self._keys and age is not None and age >= JWKS_MIN_REFRESH_INTERVAL_SECONDS
        )
        if expired or unknown_key_may_be_new:
            await self._fetch_keys()
        key = self._keys.get(key_id)
        if key is None:
            raise _invalid_token()
        return key

    async def verify(self, token: str) -> CurrentUser:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as error:
            raise _invalid_token() from error
        algorithm = header.get("alg")
        key_id = header.get("kid")
        if algorithm not in ALLOWED_ALGORITHMS or not isinstance(key_id, str):
            raise _invalid_token()

        key = await self._key_for(key_id)
        try:
            claims = jwt.decode(
                token,
                key,
                algorithms=[algorithm],
                audience=USER_AUDIENCE,
                issuer=self._issuer,
                options={"require": REQUIRED_CLAIMS},
            )
        except jwt.PyJWTError as error:
            raise _invalid_token() from error
        return _user_from_claims(claims)


def _user_from_claims(claims: dict[str, Any]) -> CurrentUser:
    if claims.get("is_anonymous") is True:
        raise _invalid_token()
    try:
        user_id = UUID(str(claims["sub"]))
    except ValueError as error:
        raise _invalid_token() from error
    metadata = claims.get("user_metadata")
    name = metadata.get("full_name") or metadata.get("name") if isinstance(metadata, dict) else None
    return CurrentUser(id=user_id, email=claims.get("email") or None, name=name)


def get_token_verifier(request: Request) -> TokenVerifier:
    verifier: TokenVerifier | None = request.app.state.token_verifier
    if verifier is None:
        raise ApiError(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "auth_not_configured",
            "Sign-in is not configured on this server.",
        )
    return verifier


# auto_error=False so a missing header gets the standard error shape below.
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
) -> CurrentUser:
    if credentials is None:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "not_authenticated", "Sign in to continue.")
    return await verifier.verify(credentials.credentials)
