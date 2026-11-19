"""The shell script beside each output that reruns its generator."""

from __future__ import annotations

import datetime as dt
import os
import shlex
import subprocess
import sys
from pathlib import Path


def _git_state(root: Path) -> str:
    try:
        run = lambda *args: subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True, check=True
        ).stdout.strip()
        commit = run("rev-parse", "--short", "HEAD")
        return f"{commit} (dirty)" if run("status", "--porcelain") else commit
    except (subprocess.CalledProcessError, OSError):
        return "unknown"


def write_script(target: Path, root: Path, outputs: list[Path], changed: bool) -> Path | None:
    """Write ``<target>.sh``. An unchanged output keeps its script and stamp."""
    if not Path(sys.argv[0]).is_file():
        print("  no regeneration script: the output was not made by a script file")
        return None
    generator = Path(os.path.relpath(Path(sys.argv[0]).resolve(), root)).as_posix()
    script = target.with_name(f"{target.name}.sh")
    if script.exists() and not changed and f"# generator: {generator}\n" in script.read_text(encoding="utf-8"):
        return script
    stamp = dt.datetime.now().astimezone().replace(microsecond=0).isoformat()
    root_from_script = Path(os.path.relpath(root, target.parent)).as_posix()
    script.write_text(
        "#!/usr/bin/env bash\n"
        f"# Regenerates {', '.join(path.name for path in outputs)}\n"
        f"# generator: {generator}\n"
        f"# generated: {stamp}  git: {_git_state(root)}\n"
        "set -euo pipefail\n"
        f'cd "$(dirname "${{BASH_SOURCE[0]}}")"/{shlex.quote(root_from_script)}\n'
        "if [ -f .venv/bin/activate ]; then source .venv/bin/activate; fi\n"
        f"python {shlex.quote(generator)}\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | 0o111)
    return script
