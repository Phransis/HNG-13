import hashlib
import re
from collections import Counter
from datetime import datetime, timezone

def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def current_utc_iso8601_z() -> str:
    now = datetime.utcnow()
    return now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

_NON_ALNUM_RE = re.compile(r'[^0-9a-zA-Z]')

def is_palindrome(value: str) -> bool:
    # Case-insensitive, ignore non-alphanumeric characters
    norm = _NON_ALNUM_RE.sub("", value).lower()
    return norm == norm[::-1]

def character_frequency_map(value: str) -> dict:
    # Count characters exactly as they appear (case-sensitive)
    return dict(Counter(value))

def word_count(value: str) -> int:
    # split on whitespace
    parts = value.strip().split()
    return 0 if parts == [''] or len(parts) == 0 and not value.strip() else len(parts)

def unique_characters(value: str) -> int:
    return len(set(value))
