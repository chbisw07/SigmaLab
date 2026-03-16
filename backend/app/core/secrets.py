from __future__ import annotations

import base64
from dataclasses import dataclass
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


class SecretsError(ValueError):
    pass


def mask_secret(value: str | None, *, keep: int = 4) -> str | None:
    """Mask a secret for display purposes.

    Example: "abcdEFGH" -> "****EFGH"
    """
    if value is None:
        return None
    v = str(value)
    if not v:
        return ""
    if keep <= 0:
        return "****"
    if len(v) <= keep:
        return "*" * len(v)
    return ("*" * (len(v) - keep)) + v[-keep:]


def _validate_fernet_key(key: str) -> bytes:
    try:
        raw = key.encode("utf-8")
        decoded = base64.urlsafe_b64decode(raw)
        if len(decoded) != 32:
            raise SecretsError("SIGMALAB_ENCRYPTION_KEY must be a valid Fernet key")
        return raw
    except Exception as e:
        raise SecretsError("SIGMALAB_ENCRYPTION_KEY must be a valid Fernet key") from e


@dataclass(frozen=True)
class SecretBox:
    """Small wrapper around Fernet encryption for storing secrets in DB JSON."""

    fernet: Fernet

    @classmethod
    def from_key(cls, key: str | None) -> "SecretBox":
        if not key:
            raise SecretsError("SIGMALAB_ENCRYPTION_KEY is required to store broker secrets in DB")
        raw = _validate_fernet_key(key)
        return cls(fernet=Fernet(raw))

    def encrypt_str(self, value: str) -> str:
        token = self.fernet.encrypt(value.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt_str(self, token: str) -> str:
        try:
            data = self.fernet.decrypt(token.encode("utf-8"))
            return data.decode("utf-8")
        except InvalidToken as e:
            raise SecretsError("Failed to decrypt broker secrets (wrong SIGMALAB_ENCRYPTION_KEY?)") from e

    def encrypt_mapping(self, values: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in values.items():
            if v is None:
                out[k] = None
            else:
                out[k] = self.encrypt_str(str(v))
        return out

    def decrypt_mapping(self, values: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in values.items():
            if v is None:
                out[k] = None
            else:
                out[k] = self.decrypt_str(str(v))
        return out

