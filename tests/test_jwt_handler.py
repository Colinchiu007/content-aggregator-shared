"""Tests for JWT handler — token creation, decoding, user extraction."""
import jwt
import pytest
from datetime import datetime, timedelta, timezone


# Patch env BEFORE any module imports
import os
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-32chr"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "15"
os.environ["REFRESH_TOKEN_EXPIRE_DAYS"] = "30"

from content_aggregator_shared.shared.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_from_token,
)


class TestCreateAccessToken:
    def test_create_basic(self):
        token = create_access_token(user_id=1, username="alice")
        assert isinstance(token, str)
        assert len(token) > 20
        payload = decode_token(token)
        assert payload["sub"] == "1"
        assert payload["username"] == "alice"
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    def test_with_custom_role(self):
        token = create_access_token(user_id=2, username="admin", role="admin")
        payload = decode_token(token)
        assert payload["role"] == "admin"

    def test_with_custom_expiry(self):
        token = create_access_token(user_id=1, username="alice", expires_delta=timedelta(hours=1))
        payload = decode_token(token)
        assert "exp" in payload

    def test_different_users_different_tokens(self):
        t1 = create_access_token(user_id=1, username="alice")
        t2 = create_access_token(user_id=2, username="bob")
        assert t1 != t2


class TestCreateRefreshToken:
    def test_create_basic(self):
        token = create_refresh_token(user_id=1)
        assert isinstance(token, str)
        payload = decode_token(token)
        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"

    def test_custom_expiry_days(self):
        token = create_refresh_token(user_id=1, expires_days=7)
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_access_vs_refresh_different(self):
        access = create_access_token(user_id=1, username="alice")
        refresh = create_refresh_token(user_id=1)
        assert access != refresh


class TestDecodeToken:
    def test_decode_valid_token(self):
        token = create_access_token(user_id=1, username="alice")
        payload = decode_token(token)
        assert payload["sub"] == "1"
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_expired_token(self):
        token = create_access_token(
            user_id=1, username="alice",
            expires_delta=timedelta(seconds=-1),
        )
        with pytest.raises(jwt.ExpiredSignatureError):
            decode_token(token)

    def test_decode_invalid_token(self):
        with pytest.raises((jwt.InvalidTokenError, jwt.DecodeError)):
            decode_token("not-a-valid-token")

    def test_decode_tampered_token(self):
        token = create_access_token(user_id=1, username="alice")
        tampered = token[:-1] + ("X" if token[-1] != "X" else "Y")
        with pytest.raises((jwt.InvalidTokenError, jwt.DecodeError)):
            decode_token(tampered)


class TestGetUserFromToken:
    def test_valid_token(self):
        token = create_access_token(user_id=42, username="charlie", role="vip")
        user = get_user_from_token(token)
        assert user is not None
        assert user["user_id"] == 42
        assert user["username"] == "charlie"
        assert user["role"] == "vip"
        assert user["type"] == "access"

    def test_expired_token_returns_none(self):
        token = create_access_token(
            user_id=1, username="alice",
            expires_delta=timedelta(seconds=-1),
        )
        assert get_user_from_token(token) is None

    def test_invalid_token_returns_none(self):
        assert get_user_from_token("garbage-token") is None

    def test_tampered_token_returns_none(self):
        token = create_access_token(user_id=1, username="alice")
        tampered = token[:-5] + "XXXXX"
        assert get_user_from_token(tampered) is None

    def test_empty_token_returns_none(self):
        assert get_user_from_token("") is None
