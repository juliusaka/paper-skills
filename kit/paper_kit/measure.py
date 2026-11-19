"""Measure the paper's text block and record it in paper_kit.toml.

Run after setup and whenever the document class or its options change:
    python -m paper_kit.measure
"""

from __future__ import annotations

import re

from . import config as config_module
from .fit import compile_probe


def main() -> None:
    config = config_module.load(prefer_cwd=True)
    values, _ = compile_probe(config, "")
    block = (
        "[page]  # written by python -m paper_kit.measure, do not edit\n"
        f"textwidth_pt = {values['textwidth']}\n"
        f"columnwidth_pt = {values['columnwidth']}\n"
        f"textheight_pt = {values['textheight']}\n"
    )
    text = config.path.read_text(encoding="utf-8")
    # Removes the header and its keys only, so comments of the next section stay.
    text = re.sub(r"^\[\s*page\s*\][^\n]*\n(?:[ \t]*\w+[ \t]*=[^\n]*(?:\n|\Z))*", "", text, flags=re.MULTILINE).rstrip()
    config.path.write_text(f"{text}\n\n{block}", encoding="utf-8")
    print(block, end="")


if __name__ == "__main__":
    main()
