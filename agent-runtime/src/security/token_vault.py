"""Local, authenticated tokenization for financial clean-room workflows."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken


class FinancialTokenVault:
    PATTERNS = {
        "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "PAN": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
        "ACCOUNT": re.compile(r"\bAccount\s*#?\s*\d{6,12}\b", re.IGNORECASE),
        "SWIFT": re.compile(r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b"),
    }

    def __init__(self, key_path: str | Path = "data/vault.key") -> None:
        self.key_path = Path(key_path)
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if self.key_path.exists():
            key = self.key_path.read_bytes()
            Fernet(key)
        else:
            key = Fernet.generate_key()
            self.key_path.write_bytes(key)
            try:
                self.key_path.chmod(0o600)
            except OSError:
                pass
        self._cipher = Fernet(key)

    def encrypt(self, value: str) -> str:
        return self._cipher.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, value: str) -> str:
        try:
            return self._cipher.decrypt(value.encode("ascii")).decode("utf-8")
        except (InvalidToken, UnicodeError) as exc:
            raise ValueError("Unable to authenticate vault ciphertext") from exc

    def redact_and_tokenize(self, text: str) -> tuple[str, dict[str, Any]]:
        token_map: dict[str, Any] = {"values": {}, "digest": ""}
        redacted = text
        for category, pattern in self.PATTERNS.items():
            index = 0

            def replace(match: re.Match[str]) -> str:
                nonlocal index
                token = f"[{category}_{index}]"
                token_map["values"][token] = self.encrypt(match.group(0))
                index += 1
                return token

            redacted = pattern.sub(replace, redacted)
        token_map["digest"] = self._map_digest(redacted, token_map["values"])
        return redacted, token_map

    def rehydrate(self, redacted_text: str, token_map: dict[str, Any]) -> str:
        values = token_map.get("values", {})
        expected = self._map_digest(redacted_text, values)
        if not hmac.compare_digest(expected, str(token_map.get("digest", ""))):
            raise ValueError("Token map authentication failed")
        restored = redacted_text
        for token, encrypted in values.items():
            restored = restored.replace(token, self.decrypt(encrypted))
        return restored

    @staticmethod
    def _map_digest(redacted_text: str, values: dict[str, str]) -> str:
        payload = json.dumps([redacted_text, values], sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()