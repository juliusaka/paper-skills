"""Measure a float against the page by compiling it alone with the paper's own preamble."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .config import Config

DEFAULT_SPECIFIER = "tbp"  # LaTeX's default for figure and table

_BEGIN_DOCUMENT = r"\begin{document}"

_QUERIES = {
    "textwidth": r"\the\textwidth",
    "columnwidth": r"\the\columnwidth",
    "textheight": r"\the\textheight",
    "textfloatsep": r"\the\dimexpr\textfloatsep\relax",
    "textfraction": r"\textfraction",
    "topfraction": r"\topfraction",
    "bottomfraction": r"\bottomfraction",
    "floatpagefraction": r"\floatpagefraction",
    "dbltopfraction": r"\dbltopfraction",
    "dblfloatpagefraction": r"\dblfloatpagefraction",
}

# Reports the box LaTeX itself places, so the measured height is the one that decides placement.
_PROBE_MACROS = r"""
\makeatletter
\let\pk@endfloatbox\@endfloatbox
\def\@endfloatbox{\pk@endfloatbox
  \typeout{PAPERKIT-height=\the\ht\@currbox}%
  \typeout{PAPERKIT-depth=\the\dp\@currbox}}
\makeatother
"""


@dataclass
class Fit:
    """Where one float lands on the page."""

    name: str
    values: dict[str, float]
    height_pt: float | None  # None for a longtable, which is not a float
    specifier: str
    star: bool  # spans both columns of a two-column page
    pages: int
    overfull: list[str]

    @property
    def share_limit_pt(self) -> float:
        """Tallest float that can still share a page with text."""
        v, spec = self.values, self.specifier
        total = v["textheight"]
        force = "!" in spec
        if self.star:
            return (1.0 if force else v["dbltopfraction"]) * total if "t" in spec else 0.0
        areas = [1.0] if "h" in spec else []
        if "t" in spec:
            areas.append(1.0 if force else v["topfraction"])
        if "b" in spec:
            areas.append(1.0 if force else v["bottomfraction"])
        if not areas:
            return 0.0
        text_room = total - v["textfloatsep"] - (0.0 if force else v["textfraction"] * total)
        return min(max(areas) * total, text_room)

    @property
    def floatpage_min_pt(self) -> float:
        """Shortest float that LaTeX allows on a float page of its own."""
        v = self.values
        return (v["dblfloatpagefraction"] if self.star else v["floatpagefraction"]) * v["textheight"]

    @property
    def placement(self) -> str:
        if self.height_pt is None:
            return "longtable"
        if "H" in self.specifier:
            return "fixed position"
        if self.height_pt > self.values["textheight"]:
            return "does not fit"
        shares = self.height_pt <= self.share_limit_pt
        own_page = "p" in self.specifier and self.height_pt >= self.floatpage_min_pt
        if shares and own_page:  # decided by where the float falls in the text
            return "shares a page or takes a float page"
        if own_page:
            return "float page of its own"
        return "shares a page with text" if shares else "deferred"

    def report(self) -> None:
        """Print the measurement and everything that needs a decision."""
        boxes = f"{len(self.overfull)} OVERFULL" if self.overfull else "no overfull boxes"
        if self.height_pt is None:
            print(f"  longtable, {self.pages} page(s), {boxes}")
        else:
            total = self.values["textheight"]
            print(
                f"  {self.height_pt:.1f} pt tall of {total:.1f} pt text block "
                f"({self.height_pt / total:.0%}), {self.placement}, {boxes}"
            )
        for box in self.overfull:
            print(f"  WARNING: too wide: {box}")
        if self.placement == "deferred":
            limit = self.share_limit_pt
            if "p" in self.specifier:
                reason = f"it needs {self.floatpage_min_pt:.1f} pt for a float page"
                action = f"Shorten it below {limit:.1f} pt."
            else:
                reason = f"the specifier [{self.specifier}] does not allow a float page"
                action = f"Add p to the specifier or shorten it below {limit:.1f} pt."
            print(
                f"  WARNING: {self.height_pt:.1f} pt is too tall to share a page (limit {limit:.1f} pt) "
                f"and {reason}. LaTeX holds it back, possibly to the end of the document. {action}"
            )
        elif self.placement == "does not fit":
            two_columns = self.values["columnwidth"] < self.values["textwidth"] * 0.99
            action = "Split it." if two_columns else "Split it or use a longtable."
            print(f"  WARNING: taller than the text block. {action}")


def preamble(config: Config) -> str:
    """The paper's preamble, so the mock-up has the same class, packages and macros."""
    if not config.tex.is_file():
        raise SystemExit(f"main file not found: {config.tex} (set tex in {config.path.name})")
    text = config.tex.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^[^%\n]*?\\begin\{document\}", text, flags=re.MULTILINE)
    if match is None:
        raise SystemExit(rf"{config.tex} has no \begin{{document}}")
    return text[: match.end() - len(_BEGIN_DOCUMENT)]


def compile_probe(
    config: Config, body: str, files: dict[str, str] | None = None, pdf_out: Path | None = None
) -> tuple[dict[str, float], str]:
    """Compile ``body`` after the paper's preamble; return the probe values and the log.

    ``pdf_out`` keeps a copy of the compiled PDF.
    """
    if shutil.which("pdflatex") is None:
        raise SystemExit("pdflatex not found: install a LaTeX distribution")
    queries = "\n".join(rf"\typeout{{PAPERKIT-{key}={value}}}" for key, value in _QUERIES.items())
    source = "\n".join([preamble(config), _PROBE_MACROS, _BEGIN_DOCUMENT, queries, body, r"\end{document}", ""])
    with tempfile.TemporaryDirectory(prefix="paper-kit-") as tmp:
        work = Path(tmp)
        for name, content in (files or {}).items():
            (work / name).write_text(content, encoding="utf-8")
        (work / "probe.tex").write_text(source, encoding="utf-8")
        # Runs in the paper's folder, so paths in its preamble resolve as in a real build.
        search = [str(work), str(config.tex.parent), os.environ.get("TEXINPUTS", "").rstrip(os.pathsep), ""]
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", f"-output-directory={work}", str(work / "probe.tex")],
            cwd=config.tex.parent,
            env={**os.environ, "TEXINPUTS": os.pathsep.join(search)},
            capture_output=True, encoding="utf-8", errors="replace", timeout=300,
        )
        log_path = work / "probe.log"
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else result.stdout
        if pdf_out is not None and result.returncode == 0 and (work / "probe.pdf").exists():
            shutil.copyfile(work / "probe.pdf", pdf_out)
    if result.returncode != 0:
        errors = [line for line in log.splitlines() if line.startswith("!")]
        raise SystemExit("does not compile with pdfLaTeX and the paper's preamble:\n  " + "\n  ".join(errors[:5] or ["see the log"]))
    values = {
        key: float(value)
        for key, value in re.findall(r"^PAPERKIT-(\w+)=([0-9.]+)(?:pt)?\s*$", log, flags=re.MULTILINE)
    }
    return values, log


def _check_page(config: Config, values: dict[str, float]) -> None:
    for key in ("textwidth", "columnwidth", "textheight"):
        if abs(config.page[f"{key}_pt"] - values[key]) > 0.01:
            raise SystemExit(
                f"the page changed: {key} is {values[key]} pt, {config.path.name} records "
                f"{config.page[f'{key}_pt']} pt. Run python -m paper_kit.measure and regenerate all figures."
            )


def measure(config: Config, name: str, fragment: str, pdf_out: Path | None = None) -> Fit | None:
    """Measure a float fragment. Returns None when pdflatex is not installed."""
    if shutil.which("pdflatex") is None:
        print("  pdflatex not found: page fit not measured")
        return None
    values, log = compile_probe(
        config,
        r"\thispagestyle{empty}\input{paperkit-fragment.tex}",  # no page number in a rendered picture
        {"paperkit-fragment.tex": fragment},
        pdf_out,
    )
    _check_page(config, values)
    height = values.get("height")
    if height is None and "longtable" not in fragment:
        raise SystemExit(f"{name}: no float found in the fragment")
    begin = re.search(r"\\begin\{(?:table|figure)(\*?)\}\s*(?:\[([^\]]*)\])?", fragment)
    pages = re.search(r"Output written .*\((\d+) page", log)
    return Fit(
        name=name,
        values=values,
        height_pt=None if height is None else height + values.get("depth", 0.0),
        specifier=(begin.group(2) if begin else None) or DEFAULT_SPECIFIER,
        star=bool(begin and begin.group(1)) and values["columnwidth"] < values["textwidth"] * 0.99,
        pages=int(pages.group(1)) if pages else 0,
        overfull=[line.strip() for line in log.splitlines() if line.startswith("Overfull \\hbox")],
    )
