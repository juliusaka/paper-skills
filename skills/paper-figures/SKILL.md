---
name: paper-figures
description: Generate a figure for a LaTeX research paper with the shared paper_kit style. Use whenever a paper figure is added, changed or regenerated. It enforces one generator script per figure, measured sizing, a colour-blind-safe palette, a reproducible save, a page-fit check and notes that keep analysis out of the prose.
---

# Paper figures

Every paper figure comes from one Python generator that uses `paper_kit.style`, and every figure on disk sits next to the script that regenerates it.

Read `paper-conventions.md` in the project root first. Do not use this skill for exploratory plots.

## Workflow

### 1. Settle what the figure is

- **Width:** `"full"`, `"column"` or `"half"`.
- **Panels:** more than seven distinguishable series in one axes means two figures.
- **Symbols:** take them from the notation in `paper-conventions.md`, never from variable names in code.

### 2. Copy a template

Copy `plot_single_axes.py` or `plot_panel_grid.py` from the `templates/` folder of the installed kit to the figure generator folder named in `paper-conventions.md` as `plot_<figure_name>.py`. The generator belongs in the project's Git repository.

### 3. Follow the rules

1. **One figure per script.** Put shared loading code in a module beside the generators.
2. **No command-line arguments.** Inputs and the figure name are constants at the top.
3. **Size with `ps.figure()`**, never `figsize=`. LaTeX then scales by 1 and labels keep their point size.
4. **Use role colours** (`ps.role("reference")`, `"model"`, `"setpoint"`, `"baseline"`, `"limit"`) for lines with a meaning. Use the default cycle only for interchangeable series.
5. **Save with `ps.save(fig, NAME, caption=CAPTION)`**, never `fig.savefig()`. If the paper uses a float specifier other than `[tbp]`, pass it as `placement=`.
6. **Place outside legends with `loc="outside lower center"`**, not `bbox_to_anchor`.
7. **Colour heatmaps with `ps.CMAP` or `ps.DENSITY_CMAP`**, never a bare colormap name.
8. **Keep reruns identical.** Set random seeds as constants and do not draw timestamps.

### 4. Run it and read the output

`save()` prints the files it wrote, then lines like these:

```
  5.147 x 3.181 in on the page (1.000 textwidth), labels 7.00 pt
  include: \includesvg[width=\textwidth]{figures/generated/example}
  254.3 pt tall of 552.7 pt text block (46%), shares a page with text, no overfull boxes
```

Treat every `WARNING:` as a real problem.

Then look at the PNG yourself, fix the generator and rerun it until none of these is wrong:

- every label, tick and legend entry is readable and overlaps nothing
- the legend covers no data
- every series can be told apart, and no lines merge into a solid block
- the figure shows the point it is meant to support

If you cannot view images, tell the user and name the PNG they need to check.

### 5. Check the fit without building the paper

Pass the caption you intend to use to `save()`. It compiles the figure's height and caption alone with the paper's preamble and reports one of these outcomes:

| Outcome | Meaning |
|---|---|
| shares a page with text | fine |
| shares a page or takes a float page | fine, the position in the text decides |
| deferred | LaTeX holds it back, possibly to the end of the document. Follow the action in the warning. |
| float page of its own | fine |
| does not fit | reduce the height or split the figure |

Size the figure for its caption, not for the text block alone. Use `[tbp]` as the float specifier. Without `p`, a tall float cannot get a page of its own.

### 6. Heatmaps

- Use `ps.DENSITY_CMAP` when empty cells exist and must read as empty, as in counts and 2-D histograms. Use `ps.CMAP` for a field defined everywhere.
- Avoid a single-hue ramp. Lightness alone resolves fewer steps than lightness plus hue.
- Take the norm's ceiling from the largest value in the interesting region, set `extend="both"` on the colorbar and let a dominant mode saturate.
- Use one shared colorbar as tall as the panels it serves. Place it after layout with `fig.add_axes`, from the axes' bounding boxes.

### 7. Keep the figure as vector graphics

The paper includes the SVG. The PNG is only for review.

- Use the include line that `save()` prints, without a file extension. The width must match the size the figure was made for, or LaTeX rescales its labels:

  | `ps.figure(width=...)` | Environment | Include width |
  |---|---|---|
  | `"full"` | `figure`, or `figure*` in a two-column paper | `\textwidth` |
  | `"column"` | `figure` | `\columnwidth` |
  | `"half"` | a subfigure of `0.49\columnwidth` | `\linewidth` |

- The `svg` package converts the SVG with Inkscape during the build, so build with `latexmk` and `-shell-escape`. The installed `.latexmkrc` sets this.
- Commit the SVG, the PNG and the `.sh`. Do not commit the `svg-inkscape/` folder, which the build regenerates.
- `paper_kit` stores labels as outlines, so the figure does not depend on installed fonts. Figure math therefore cannot use the paper's LaTeX macros or `siunitx`. Write `\mathrm` instead of `\text`, and units as plain text such as `(K)`.
- Keep hand-drawn diagrams as editable SVG files in the repository as well.
- Use a raster image only for content that is a raster, such as a photo. For a heatmap with very many cells, set `rasterized=True` on that artist only, so axes and labels stay vector graphics.
- If the journal's build system does not allow `-shell-escape`, submit the PDF files from `svg-inkscape/` and include them with `\includegraphics`. Do this in a submission copy and keep `\includesvg` in the source.

### 8. Write three separate texts

**In the running text, one or two lines:** what the figure shows and the one point it supports.

**In a comment block above the figure:** details, measured numbers, caveats and discarded alternatives. Open it with a stamp:

```latex
% figure notes -- generated: 2026-01-15T14:44:36+0100  git: 4cbe9b1 (dirty)
% - The colour scale is logarithmic and shared across panels.
% - Failed runs are excluded, so each panel normalizes over its completed runs.
\begin{figure}[tbp]
    \centering
    \includesvg[width=\textwidth]{figures/generated/example}
    \caption{...}\label{fig:example}
\end{figure}
```

Get the stamp from `date +%Y-%m-%dT%H:%M:%S%z` and `git rev-parse --short HEAD`, and append `(dirty)` when `git status --porcelain` prints anything. When you regenerate a figure, update the stamp and revise the existing block.

**In the caption, two sentences:** what the figure is, and the one thing a reader needs to read its axes. Method and findings go in the notes.

## Changing the style or the page

- Put a project-wide style change in `[style]` in `paper_kit.toml`, then regenerate every figure.
- After a change to the document class or its options, run `python -m paper_kit.measure`, then regenerate every figure.

## Anti-patterns

| Don't | Why |
|---|---|
| `fig.savefig(...)` | no regeneration script and no fit check |
| `figsize=(6, 4)` | LaTeX rescales the figure, so label sizes no longer match |
| `bbox_inches="tight"` | the saved width is no longer the designed width |
| one script writing several figures | one figure cannot be rerun alone |
| including the PNG in the paper | text and lines blur when zoomed or printed |
| committing `svg-inkscape/` | it is build output and goes stale |
| `cmap="viridis"` on a density map | empty cells become the darkest ink on the page |
| `vmax=1.0` on a density with one huge mode | the structure lands in the palest tenth of the scale |
| an analysis paragraph added with the figure | the prose belongs to the author, the analysis belongs in the notes |
| a caption that explains the method | it costs page space and few people read it |
| notes without date and commit | they cannot be matched to the figure on disk |
