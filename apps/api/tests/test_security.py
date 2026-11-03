import asyncio
import hashlib
import hmac
import json
import time
from typing import Any
from uuid import uuid4

import httpx
import jwt
import pytest
from app.core.errors import ApiError
from app.core.security import (
    JWKS_MAX_AGE_SECONDS,
    JWKS_MIN_REFRESH_INTERVAL_SECONDS,
    CurrentUser,
    TokenVerifier,
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from jwt.algorithms import ECAlgorithm, RSAAlgorithm

ISSUER = "https://project.supabase.co/auth/v1"
EC_KEY = ec.generate_private_key(ec.SECP256R1())
RSA_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER_EC_KEY = ec.generate_private_key(ec.SECP256R1())


def jwks() -> dict[str, Any]:
    ec_jwk = json.loads(ECAlgorithm.to_jwk(EC_KEY.public_key()))
    rsa_jwk = json.loads(RSAAlgorithm.to_jwk(RSA_KEY.public_key()))
    return {
        "keys": [
            {**ec_jwk, "kid": "ec-1", "alg": "ES256", "use": "sig"},
            {**rsa_jwk, "kid": "rsa-1", "alg": "RS256", "use": "sig"},
        ]
    }


def claims(**overrides: Any) -> dict[str, Any]:
    now = int(time.time())
    base = {
        "iss": ISSUER,
        "aud": "authenticated",
        "sub": str(uuid4()),
        "iat": now,
        "exp": now + 3600,
        "role": "authenticated",
        "email": "ayesha@example.com",
        "user_metadata": {"full_name": "Ayesha Khan"},
    }
    return {**base, **overrides}


def sign(payload: dict[str, Any], key: Any = EC_KEY, algorithm: str = "ES256", kid: str = "ec-1") -> str:
    return jwt.encode(payload, key, algorithm=algorithm, headers={"kid": kid})


class Harness:
    def __init__(self, status_code: int = 200) -> None:
        self.status_code = status_code
        self.fetches = 0
        self.now = 1000.0
        self.keys: Any = jwks()

    def _respond(self, request: httpx.Request) -> httpx.Response:
        self.fetches += 1
        assert str(request.url) == f"{ISSUER}/.well-known/jwks.json"
        return httpx.Response(self.status_code, json=self.keys)

    def verifier(self) -> TokenVerifier:
        http = httpx.AsyncClient(transport=httpx.MockTransport(self._respond))
        return TokenVerifier(ISSUER, http, clock=lambda: self.now)


def verify(token: str, harness: Harness | None = None) -> CurrentUser:
    return asyncio.run((harness or Harness()).verifier().verify(token))


def assert_rejected(token: str) -> None:
    with pytest.raises(ApiError) as caught:
        verify(token)
    assert caught.value.status_code == 401
    assert caught.value.code == "invalid_token"


def test_accepts_es256() -> None:
    payload = claims()

    user = verify(sign(payload))

    assert str(user.id) == payload["sub"]
    assert user.email == "ayesha@example.com"
    assert user.name == "Ayesha Khan"


def test_accepts_rs256() -> None:
    assert verify(sign(claims(), RSA_KEY, "RS256", "rsa-1")).email == "ayesha@example.com"


def test_name_and_email_are_optional() -> None:
    payload = claims()
    del payload["user_metadata"]
    del payload["email"]

    user = verify(sign(payload))

    assert user.name is None
    assert user.email is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": int(time.time()) - 10},
        {"aud": "anon"},
        {"iss": "https://other-project.supabase.co/auth/v1"},
        {"sub": "not-a-uuid"},
        {"is_anonymous": True},
    ],
    ids=["expired", "anon-audience", "other-issuer", "bad-subject", "anonymous-user"],
)
def test_rejects_bad_claims(overrides: dict[str, Any]) -> None:
    assert_rejected(sign(claims(**overrides)))


@pytest.mark.parametrize("missing", ["exp", "iat", "sub", "aud", "iss"])
def test_rejects_missing_required_claim(missing: str) -> None:
    payload = claims()
    del payload[missing]

    assert_rejected(sign(payload))


def test_rejects_signature_from_another_key() -> None:
    assert_rejected(sign(claims(), OTHER_EC_KEY))


def test_rejects_tampered_payload() -> None:
    header, _, signature = sign(claims()).split(".")
    forged = jwt.utils.base64url_encode(json.dumps(claims(sub=str(uuid4()))).encode()).decode()

    assert_rejected(f"{header}.{forged}.{signature}")


def test_rejects_unsigned_token() -> None:
    assert_rejected(jwt.encode(claims(), key="", algorithm="none", headers={"kid": "ec-1"}))


def test_rejects_algorithm_confusion_with_public_key_as_secret() -> None:
    """Classic attack: sign with HS256 using the published public key as the secret."""
    public_key = RSA_KEY.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    encode = jwt.utils.base64url_encode
    header = encode(json.dumps({"alg": "HS256", "kid": "rsa-1"}).encode())
    payload = encode(json.dumps(claims()).encode())
    signature = encode(hmac.new(public_key, header + b"." + payload, hashlib.sha256).digest())

    assert_rejected(f"{header.decode()}.{payload.decode()}.{signature.decode()}")


def test_rejects_shared_secret_tokens() -> None:
    assert_rejected(jwt.encode(claims(), "a-long-enough-shared-secret-value-1234567", algorithm="HS256"))


@pytest.mark.parametrize("token", ["", "garbage", "a.b.c"])
def test_rejects_malformed_tokens(token: str) -> None:
    assert_rejected(token)


def test_rejects_token_without_key_id() -> None:
    assert_rejected(jwt.encode(claims(), EC_KEY, algorithm="ES256"))


def test_keys_are_cached_between_requests() -> None:
    harness = Harness()
    verifier = harness.verifier()

    async def run() -> None:
        await verifier.verify(sign(claims()))
        await verifier.verify(sign(claims()))

    asyncio.run(run())

    assert harness.fetches == 1


def test_keys_are_refetched_once_too_old() -> None:
    harness = Harness()
    verifier = harness.verifier()

    async def run() -> None:
        await verifier.verify(sign(claims()))
        harness.now += JWKS_MAX_AGE_SECONDS
        await verifier.verify(sign(claims()))

    asyncio.run(run())

    assert harness.fetches == 2


def test_revoked_key_stops_working_after_refresh() -> None:
    harness = Harness()
    verifier = harness.verifier()

    async def run() -> None:
        await verifier.verify(sign(claims()))
        harness.keys = {"keys": []}
        harness.now += JWKS_MAX_AGE_SECONDS
        await verifier.verify(sign(claims()))

    with pytest.raises(ApiError) as caught:
        asyncio.run(run())

    assert caught.value.code == "invalid_token"


@pytest.mark.parametrize("body", [["not", "an", "object"], {"keys": [{"kty": "nonsense"}]}])
def test_malformed_key_response_is_a_503(body: Any) -> None:
    harness = Harness()
    harness.keys = body

    with pytest.raises(ApiError) as caught:
        verify(sign(claims()), harness)

    assert caught.value.status_code == 503
    assert caught.value.code == "auth_unavailable"


def test_unknown_key_id_cannot_force_a_fetch_on_every_request() -> None:
    harness = Harness()
    verifier = harness.verifier()

    async def run() -> None:
        await verifier.verify(sign(claims()))
        for _ in range(5):
            with pytest.raises(ApiError):
                await verifier.verify(sign(claims(), kid="made-up"))

    asyncio.run(run())

    assert harness.fetches == 1


def test_new_key_is_picked_up_after_the_refresh_interval() -> None:
    harness = Harness()
    verifier = harness.verifier()

    async def run() -> None:
        await verifier.verify(sign(claims()))
        rotated = json.loads(ECAlgorithm.to_jwk(OTHER_EC_KEY.public_key()))
        harness.keys = {"keys": [{**rotated, "kid": "ec-2", "alg": "ES256"}]}
        harness.now += JWKS_MIN_REFRESH_INTERVAL_SECONDS
        await verifier.verify(sign(claims(), OTHER_EC_KEY, kid="ec-2"))

    asyncio.run(run())

    assert harness.fetches == 2


def test_supabase_outage_is_a_503_not_a_401() -> None:
    with pytest.raises(ApiError) as caught:
        verify(sign(claims()), Harness(status_code=500))

    assert caught.value.status_code == 503
    assert caught.value.code == "auth_unavailable"
