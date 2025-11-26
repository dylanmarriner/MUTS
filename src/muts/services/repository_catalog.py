from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class FileSummary:
    path: Path
    summary: str
    display: str


@dataclass
class DirectoryCatalog:
    name: str
    files: List[FileSummary]
    readme: str | None
    diagram: str | None


class RepositoryCatalogService:
    TARGETS = [
        "core",
        "database",
        "docs",
        "installers",
        "security",
        "simulators",
        "tools",
        "ui",
    ]

    def __init__(self, base: Path | None = None) -> None:
        self.base = (base or Path(__file__).resolve().parents[2]).resolve()

    def catalog(self) -> List[DirectoryCatalog]:
        catalogs: List[DirectoryCatalog] = []
        for name in self.TARGETS:
            dir_path = self.base / name
            if not dir_path.exists():
                continue
            files = []
            for entry in sorted(dir_path.iterdir()):
                if entry.is_file():
                    files.append(
                        FileSummary(
                            path=entry,
                            summary=self._extract_doc(entry) or "",
                            display=str(entry.relative_to(self.base)),
                        )
                    )
            catalogs.append(
                DirectoryCatalog(
                    name=name,
                    files=files,
                    readme=self._load_document(dir_path, prefixes=("readme",)) or None,
                    diagram=self._load_document(dir_path, contains=("diagram", "diagram")),
                )
            )
        return catalogs

    def _extract_doc(self, path: Path) -> str | None:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return None
        lines = text.strip().splitlines()
        if not lines:
            return None
        first = lines[0].strip()
        if first.startswith('"""') or first.startswith("'''"):
            doc_lines = [first.strip('"""').strip("'''")]
            for line in lines[1:]:
                if line.strip().endswith('"""') or line.strip().endswith("'''"):
                    doc_lines.append(line.strip().strip('"""').strip("'''"))
                    break
                doc_lines.append(line.strip())
            return " ".join(part for part in doc_lines if part).strip()
        return first[:160]

    def _load_document(
        self,
        directory: Path,
        prefixes: Iterable[str] = (),
        contains: Iterable[str] = (),
        max_lines: int = 25,
    ) -> str | None:
        for entry in sorted(directory.iterdir()):
            if not entry.is_file():
                continue
            name = entry.name.lower()
            if prefixes and any(name.startswith(prefix) for prefix in prefixes):
                return self._read_lines(entry, max_lines)
            if contains and any(keyword in name for keyword in contains):
                return self._read_lines(entry, max_lines)
        return None

    def _read_lines(self, path: Path, max_lines: int) -> str:
        try:
            with path.open(encoding="utf-8", errors="ignore") as fh:
                lines = [next(fh).rstrip() for _ in range(max_lines)]
        except StopIteration:
            pass
        except Exception:
            return ""
        return "\n".join(lines)
