"""Tests for password hashing utilities."""

import pytest

from app.auth.password import hash_password, verify_password


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """hash_password should return a string."""
        result = hash_password("testpassword123")
        assert isinstance(result, str)

    def test_hash_password_is_bcrypt_format(self):
        """hash_password should return a bcrypt hash."""
        result = hash_password("testpassword123")
        # bcrypt hashes start with $2b$
        assert result.startswith("$2b$")

    def test_hash_password_includes_rounds(self):
        """hash_password should use 12 rounds as configured."""
        result = hash_password("testpassword123")
        # Format: $2b$12$...
        assert "$2b$12$" in result

    def test_hash_password_different_each_time(self):
        """hash_password should produce different hashes for the same password (due to salt)."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """verify_password should return True for correct password."""
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """verify_password should return False for incorrect password."""
        password = "testpassword123"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_case_sensitive(self):
        """verify_password should be case-sensitive."""
        password = "TestPassword123"
        hashed = hash_password(password)
        assert verify_password("testpassword123", hashed) is False
        assert verify_password("TESTPASSWORD123", hashed) is False
        assert verify_password("TestPassword123", hashed) is True

    def test_hash_password_handles_unicode(self):
        """hash_password should handle unicode characters."""
        password = "päßwörd123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_hash_password_handles_empty_string(self):
        """hash_password should handle empty string."""
        password = ""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
        assert verify_password("notempty", hashed) is False

    def test_hash_password_handles_special_characters(self):
        """hash_password should handle special characters."""
        password = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_hash_password_rejects_long_passwords(self):
        """hash_password should raise ValueError for passwords over 72 bytes."""
        # bcrypt has a 72-byte limit
        password = "a" * 100
        with pytest.raises(ValueError, match="password cannot be longer than 72 bytes"):
            hash_password(password)

    def test_hash_password_accepts_72_byte_passwords(self):
        """hash_password should accept passwords up to 72 bytes."""
        password = "a" * 72
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True
