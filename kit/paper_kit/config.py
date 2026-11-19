"""Find and read the project's paper_kit.toml."""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

FILENAME = "paper_kit.toml"


@dataclass(frozen=True)
class Config:
    path: Path
    data: dict

    @property
    def root(self) -> Path:
        return self.path.parent

    def _paper_path(self, key: str) -> Path:
        return (self.root / self.data["paper"][key]).resolve()

    @property
    def tex(self) -> Path:
        return self._paper_path("tex")

    @property
    def figures_dir(self) -> Path:
        return self._paper_path("figures_dir")

    @property
    def tables_dir(self) -> Path:
        return self._paper_path("tables_dir")

    @property
    def figure_formats(self) -> tuple[str, ...]:
        return tuple(self.data["paper"].get("figure_formats", ("svg", "png")))

    @property
    def rc_overrides(self) -> dict:
        return self.data.get("style", {})

    @property
    def page(self) -> dict:
        if "page" not in self.data:
            raise SystemExit(f"{self.path} has no [page] section; run: python -m paper_kit.measure")
        return self.data["page"]


def _find(prefer_cwd: bool) -> Path:
    if env := os.environ.get("PAPER_KIT_CONFIG"):
        path = Path(env).resolve()
        if not path.is_file():
            raise SystemExit(f"PAPER_KIT_CONFIG points to a missing file: {path}")
        return path
    starts = [Path.cwd()]
    if sys.argv and sys.argv[0]:
        starts.insert(len(starts) if prefer_cwd else 0, Path(sys.argv[0]).resolve().parent)
    for start in starts:
        for folder in (start, *start.parents):
            if (folder / FILENAME).is_file():
                return folder / FILENAME
    raise SystemExit(f"no {FILENAME} found above the script or the working directory")


def load(prefer_cwd: bool = False) -> Config:
    """Read the config above the running script, or above the working directory first."""
    path = _find(prefer_cwd)
    return Config(path, tomllib.loads(path.read_text(encoding="utf-8")))
