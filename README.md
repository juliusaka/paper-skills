# Paper skills

Agent skills for generating figures and tables in LaTeX research papers, with a small Python kit.

**Agents:** to install this into a project, follow [SETUP.md](SETUP.md).

## Install

Give your coding agent this prompt from the root of your paper project:

```text
Install the paper skills from https://github.com/juliusaka/paper-skills into this project. Follow SETUP.md in that repository.
```

## Skills

| Skill | Use it to |
|---|---|
| `paper-figures` | generate figures with one script per figure and one consistent style |
| `paper-tables` | generate tables from data with one script per table |

## What the kit does

- Keeps figures as vector graphics: Python writes SVG, and Inkscape converts it during the LaTeX build.
- Sizes figures from the measured text block of your paper, so labels keep their point size in the PDF.
- Uses a colour-blind-safe palette with fixed colours for reference, model, setpoint, baseline and limit lines.
- Saves each figure and table next to a shell script that reruns its generator.
- Compiles a single figure or table with your paper's preamble and reports where it lands on the page, without building the paper.

## What your project gets

| File | Purpose |
|---|---|
| `paper_kit.toml` | paths, figure formats and the measured page |
| `paper-conventions.md` | notation, sources, exclusions and build settings of your paper |
| `.latexmkrc` | the build settings that let LaTeX call Inkscape |
| `tools/paper-kit/` | the Python kit and generator templates |
| your agent's skill directory | the two skills |

## Suggested project layout

Keep the paper and everything that produces its content in one Git repository:

```text
my-project/
├── paper/            the paper or thesis: main.tex, generated figures and tables
├── code/             the code you develop, as a folder or a Git submodule
├── analysis/         scripts that produce results with that code
├── paper-scripts/    the figure and table generators
├── tools/paper-kit/
└── paper_kit.toml
```

The folder names are suggestions. The `.sh` beside each figure and table names its generator, so any generator folder in the repository works.

## Requirements

Python 3.11 or newer, a LaTeX distribution with `pdflatex`, `latexmk` and the `svg` package, and Inkscape. The page checks compile with pdfLaTeX, so papers that need XeLaTeX or LuaLaTeX are not supported.

## Possible future work

- Make line series reliably distinct in greyscale: give each series its own dash pattern that does not shrink with thin lines, limit the series per axes to the number of patterns, draw the reference in solid black, and hatch filled marks. The `ieee` style of [SciencePlots](https://github.com/garrettj403/SciencePlots) pairs colours with line styles in this way.

## License

[MIT](LICENSE)
