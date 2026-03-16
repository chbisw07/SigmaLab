from __future__ import annotations

import pytest
from cryptography.fernet import Fernet

from app.core.secrets import SecretBox, SecretsError, mask_secret


def test_mask_secret_basic() -> None:
    assert mask_secret(None) is None
    assert mask_secret("") == ""
    assert mask_secret("abcd", keep=4) == "****"
    assert mask_secret("abcdefgh", keep=4) == "****efgh"
    assert mask_secret("abcdefgh", keep=0) == "****"


def test_secretbox_requires_valid_fernet_key() -> None:
    with pytest.raises(SecretsError, match="ENCRYPTION_KEY"):
        SecretBox.from_key(None)
    with pytest.raises(SecretsError, match="Fernet"):
        SecretBox.from_key("not-a-valid-key")


def test_secretbox_encrypt_decrypt_roundtrip() -> None:
    key = Fernet.generate_key().decode("utf-8")
    box = SecretBox.from_key(key)
    enc = box.encrypt_mapping({"api_key": "k", "access_token": "t", "none": None})
    assert enc["api_key"] != "k"
    assert enc["access_token"] != "t"
    dec = box.decrypt_mapping(enc)
    assert dec == {"api_key": "k", "access_token": "t", "none": None}

