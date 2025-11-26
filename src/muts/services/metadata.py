from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

BASE_DIR = Path(__file__).resolve().parents[3]
PATTERNS = ["src/*.py", "docs/*.md", "README.md"]


class MetadataService:
    def __init__(self) -> None:
        self._patterns = PATTERNS

    def discover(self, limit: int | None = None) -> list[dict[str, Iterable[str] | str]]:
        entries: list[dict[str, Iterable[str] | str]] = []
        for pattern in self._patterns:
            for path in sorted(BASE_DIR.glob(pattern)):
                if not path.is_file():
                    continue
                entries.append(self._summarize(path))
                if limit and len(entries) >= limit:
                    return entries[:limit]
        return entries

    def _summarize(self, path: Path) -> dict[str, Iterable[str] | str]:
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        doc = ""
        lines = text.splitlines()
        if lines and lines[0].startswith(('"""', "'''")):
            quote = lines[0][:3]
            doc_lines = []
            for line in lines:
                trimmed = line.strip()
                if trimmed.startswith(quote):
                    trimmed = trimmed.strip(quote)
                if trimmed.endswith(quote):
                    trimmed = trimmed.rstrip(quote)
                if trimmed:
                    doc_lines.append(trimmed)
                if line.strip().endswith(quote):
                    break
            doc = " ".join(doc_lines)[:240]

        classes = re.findall(r"class\s+([A-Za-z_][A-Za-z0-9_]*)", text)
        functions = re.findall(r"def\s+([A-Za-z_][A-Za-z0-9_]*)", text)

        return {
            "path": str(path.relative_to(BASE_DIR)),
            "doc": doc,
            "classes": classes,
            "functions": functions,
        }
