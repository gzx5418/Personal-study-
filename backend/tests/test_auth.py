from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def users_file(tmp_path):
    return tmp_path / "users.json"


class TestPasswordHash:
    def test_hash_consistent(self):
        from auth import _hash_password
        h1 = _hash_password("test123")
        h2 = _hash_password("test123")
        assert h1 == h2

    def test_hash_different_passwords(self):
        from auth import _hash_password
        h1 = _hash_password("abc")
        h2 = _hash_password("xyz")
        assert h1 != h2

    def test_hash_returns_string(self):
        from auth import _hash_password
        result = _hash_password("test")
        assert isinstance(result, str)
        assert len(result) == 64


class TestToken:
    def test_create_and_verify(self):
        from auth import create_token, verify_token
        token = create_token("user_001")
        user_id = verify_token(token)
        assert user_id == "user_001"

    def test_verify_invalid_token(self):
        from auth import verify_token
        result = verify_token("invalid.token.here")
        assert result is None

    def test_verify_expired_token(self):
        import jwt as pyjwt
        from auth import JWT_SECRET, JWT_ALGORITHM, verify_token
        payload = {"sub": "user_001", "iat": time.time() - 100, "exp": time.time() - 10}
        token = pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        result = verify_token(token)
        assert result is None


class TestUserRegistration:
    def test_register_new_user(self, users_file):
        with patch("auth.USERS_FILE", users_file):
            from auth import register_user
            result = register_user("new_user", "password123", "测试用户")
            assert result["user_id"] == "new_user"
            assert result["name"] == "测试用户"
            assert "token" in result

    def test_register_duplicate_user(self, users_file):
        with patch("auth.USERS_FILE", users_file):
            from auth import register_user
            register_user("dup_user", "pass1")
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                register_user("dup_user", "pass2")
            assert exc_info.value.status_code == 409

    def test_register_saves_to_file(self, users_file):
        with patch("auth.USERS_FILE", users_file):
            from auth import register_user, _load_users, _hash_password
            register_user("file_user", "pass1")
            users = _load_users()
            assert "file_user" in users


class TestUserAuthentication:
    def test_authenticate_valid(self, users_file):
        with patch("auth.USERS_FILE", users_file):
            from auth import register_user, authenticate_user
            register_user("auth_user", "correct_pass")
            result = authenticate_user("auth_user", "correct_pass")
            assert result["user_id"] == "auth_user"
            assert "token" in result

    def test_authenticate_wrong_password(self, users_file):
        with patch("auth.USERS_FILE", users_file):
            from auth import register_user, authenticate_user
            register_user("auth_user2", "correct_pass")
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                authenticate_user("auth_user2", "wrong_pass")
            assert exc_info.value.status_code == 401

    def test_authenticate_nonexistent_user(self, users_file):
        with patch("auth.USERS_FILE", users_file):
            from auth import authenticate_user
            from fastapi import HTTPException
            with pytest.raises(HTTPException) as exc_info:
                authenticate_user("no_such_user", "pass")
            assert exc_info.value.status_code == 401


class TestUsersFile:
    def test_load_empty_when_no_file(self, tmp_path):
        fake_file = tmp_path / "nonexistent.json"
        with patch("auth.USERS_FILE", fake_file):
            from auth import _load_users
            users = _load_users()
            assert users == {}

    def test_save_and_load(self, tmp_path):
        fake_file = tmp_path / "test_users.json"
        with patch("auth.USERS_FILE", fake_file):
            from auth import _save_users, _load_users
            data = {"user1": {"password_hash": "abc", "name": "User 1"}}
            _save_users(data)
            loaded = _load_users()
            assert loaded == data
