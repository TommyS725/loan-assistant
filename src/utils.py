import json
import re
import unicodedata
from typing import Any
import re


def normalize_text(s: Any) -> str:
    return re.sub(r"(?<!\\)([%$])", r"\\\1", s)
