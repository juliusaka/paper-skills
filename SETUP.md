# Setup instructions for an agent

Install the paper skills into the user's project. Work through the steps in order. Do not overwrite an existing file without asking, and do not commit unless the user asks.

## 1. Fetch this repository

Clone it into a temporary directory outside the project. Below, `<clone>` is that directory and `<project>` is the root of the user's project.

## 2. Copy the files

| From | To |
|---|---|
| `<clone>/skills/*` | the skill directory of the agent in use: `.claude/skills/` for Claude Code, `.github/skills/` for GitHub Copilot, otherwise the directory that agent documents |
| `<clone>/kit/` | `<project>/tools/paper-kit/` |
| `<clone>/kit/project/paper_kit.toml` | `<project>/paper_kit.toml` |
| `<clone>/kit/project/paper-conventions.md` | `<project>/paper-conventions.md` |
| `<clone>/kit/project/.latexmkrc` | next to the main `.tex` file. If one exists, add its settings to the existing file. |

If the project has no layout yet, propose the one in the README's "Suggested project layout". Never move existing files without asking.

## 3. Install the kit

The kit needs Python 3.11 or newer. If the project has no Python environment, create `.venv` in the project root and add `.venv/` to `.gitignore`. Activate the environment for all commands below. The generated regeneration scripts activate `.venv` as well.

Install `tools/paper-kit` as an editable package:

```bash
uv add --editable ./tools/paper-kit     # only if the project root has a pyproject.toml managed with uv
pip install -e ./tools/paper-kit        # otherwise, inside the active environment
```

## 4. Fill in `paper_kit.toml`

- `tex`: the main file, which contains `\documentclass` and `\begin{document}`.
- `figures_dir` and `tables_dir`: the existing folders if there are any.

## 5. Prepare the LaTeX build

- Check that `pdflatex`, `latexmk` and `inkscape` are installed. Do not install system packages without asking.
- If `pdflatex` is missing, stop and tell the user. If only `latexmk` or `inkscape` is missing, continue, skip the build in step 8 and list it as unverified in your report.
- Add `\usepackage{svg}` to the paper's preamble if it is missing.
- Add `**/svg-inkscape/` to the project's `.gitignore`.

## 6. Measure the page

Run this from the project root:

```bash
python -m paper_kit.measure
```

It writes the text block dimensions into `paper_kit.toml`. The kit compiles with pdfLaTeX and without `-shell-escape`. If the preamble does not compile that way, for example because it needs XeLaTeX, LuaLaTeX or `minted`, report the error to the user.

## 7. Fill in `paper-conventions.md`

Fill in what the paper and the repository show: notation, float specifier, generator folders and sources of results. Ask the user only for what you cannot find, in one short list. Always ask what must not appear in the paper. Remove sections that do not apply.

## 8. Verify

Run the templates from the project root, then delete the example files they wrote to `figures_dir` and `tables_dir`:

```bash
python tools/paper-kit/templates/plot_single_axes.py
python tools/paper-kit/templates/plot_panel_grid.py
python tools/paper-kit/templates/table_from_csv.py
```

Each run must print a line with the height in points and no `WARNING:`. Open one generated PNG and check it.

Before you delete the examples, confirm that Inkscape converts an SVG. Put a temporary copy of the main file next to the original, add the include line that `plot_single_axes.py` printed, change to that folder and run `latexmk <copy>.tex`. `latexmk` reads `.latexmkrc` from the working directory. Delete the copy and its build files afterwards.

## 9. Report

Delete the temporary clone. Tell the user which files you added, the measured text width and height, anything you could not verify, and any open questions from step 7.

## Updating

Replace the skills and `tools/paper-kit/` with the new versions. Keep `paper_kit.toml` and `paper-conventions.md`.
