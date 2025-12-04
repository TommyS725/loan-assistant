import json
import re
import unicodedata
from typing import Any
import re


def normalize_text(s: Any) -> str:
    # Normalize special characters (% or $) that are not already escaped
    s = re.sub(r"(?<!\\)([%$])", r"\\\1", str(s))

    # Add extra newline after the last list item (line starting with '-')
    # Find all matches where line starts with '-' and ends with '\n'
    matches = list(re.finditer(r"(- [^\n]+?\n)(?!- )", s))
    if matches:
        last = matches[-1]
        start, end = last.span()
        # Insert extra newline after the last match
        s = s[:end] + "\n" + s[end:]
    return s
