---
name: paper-tables
description: Generate a table for a LaTeX research paper with paper_kit. Use whenever a paper table is added, changed or regenerated, or to find out whether a table fits the page. It enforces one generator script per table, LaTeX built in the generator, a page-fit check without building the paper and notes that keep analysis out of the prose.
---

# Paper tables

Every paper table comes from a script, and every table on disk sits next to a `.sh` that reruns that script. A number typed into a `tabular` disagrees with the data after the next rerun, and nothing reports it.

Read `paper-conventions.md` in the project root first.

## Workflow

### 1. Settle what the table is

- **Source:** which file holds the numbers, and which rows and columns does the table show?
- **Length:** a table that cannot fit on one page must be a `longtable`. A `longtable` is not a float and must not sit inside a brace group. It does not work in two-column mode, so split the table there.
- **Symbols:** take them from the notation in `paper-conventions.md`, never from variable names in code.
- **Exclusions:** check what must not appear. If a group of channels has no notation in the paper, summarize it in the caption.

### 2. Write the generator

Copy `table_from_csv.py` from the `templates/` folder of the installed kit to the table generator folder named in `paper-conventions.md` as `table_<table_name>.py`. The generator belongs in the project's Git repository.

1. **One table per script.**
2. **No command-line arguments.** Inputs, the slice (`FILTERS`, `SORT_BY`) and the output name are constants at the top.
3. **Build the LaTeX in the generator.** The column list is the layout. Do not add a template file.
4. **Save with `tables.save(tex, NAME)`**, never `path.write_text()`.
5. **Look up columns by name and raise when one is missing** (`tables.require_columns`). Positions relabel a table silently when the source changes.
6. **Sort completely**, so the row order does not change between runs.
7. **Recompute a number when the stored copy is not what the paper reports**, and say why in the docstring.
8. **Start the output with `tables.provenance(__file__, SOURCE)`.**
9. **Use the shared formatters** `num`, `num_or_sci`, `sci_math`, `latex_escape` and `tex_wrap`. Add a missing one to the kit, not to a generator.
10. **Use the rule commands of the document class.** If `save()` reports an undefined command, check `paper-conventions.md`.

### 3. Run it and read the output

```
wrote paper/tables/example.tex
wrote paper/tables/example.png
wrote paper/tables/example.sh
  299.8 pt tall of 552.7 pt text block (54%), shares a page with text, no overfull boxes
```

`save()` compiles the table alone with the paper's preamble and renders it as a PNG. Treat every `WARNING:` as a real problem.

Then look at the PNG yourself, fix the generator and rerun it until none of these is wrong:

- every heading and cell is readable, and nothing wraps or runs into the next column
- units sit in the headings, and numbers in a column have the same precision
- missing values are marked, not empty

If you cannot view images, tell the user and name the PNG they need to check. For a `longtable` the PNG shows its first page only.

### 4. Check the fit without building the paper

| Outcome | What LaTeX does | Action |
|---|---|---|
| shares a page with text | places it with the text | none |
| shares a page or takes a float page | decides by the position in the text | none |
| deferred | holds it back, possibly to the end of the document | add `p` to the float specifier if it is missing, otherwise drop rows or columns, or split the table |
| float page of its own | gives it a separate page | none |
| does not fit | cannot place it as a float | split the table, or use a `longtable` in a one-column paper |

Use `[tbp]` as the float specifier. Never pad a caption to push a deferred table onto a float page. Shorten the table.

An `Overfull \hbox` means the table is too wide. Ignore underfull boxes.

### 5. Include it

```latex
\input{tables/<table_name>.tex}
```

The fragment carries its own `table` environment, `\caption` and `\label`. Commit the `.tex`, the PNG and the `.sh`.

### 6. Write three separate texts

**In the running text, one or two lines:** what the table lists and where it comes from.

**In a comment block above the `\input`:** the slice the numbers cover, the cross-check that supports them, what was left out and why, and anything a reader could misread. Open it with a stamp:

```latex
% table notes -- generated: 2026-01-15T16:07:31+0100  git: e651d1a (dirty)
% - Means are over runs, not over cases.
% - Cross-check: the first row matches the training log.
\input{tables/example.tex}
```

Get the stamp from `date +%Y-%m-%dT%H:%M:%S%z` and `git rev-parse --short HEAD`, and append `(dirty)` when `git status --porcelain` prints anything. When you regenerate a table, update the stamp and revise the existing block.

**In the caption, two sentences:** what the table is, and the one thing a reader needs to read its rows. Method and findings go in the notes.

## When the document class changes

Run `python -m paper_kit.measure` and regenerate all tables and figures. `save()` stops with a message if the recorded page no longer matches the paper.

## Anti-patterns

| Don't | Why |
|---|---|
| type a number into a `tabular` | it silently disagrees with the data after a rerun |
| `path.write_text(table)` | the fit question stays unanswered |
| build the whole paper to check a table | `save()` answers in seconds |
| read a height inside the text block as "it fits" | a table can still be deferred |
| a template file beside the generator | the layout then lives in two places |
| index a row by position | a new source column relabels the table silently |
| a caption that explains the method | it costs page space and few people read it |
| one script writing two tables | one table cannot be rerun alone |
| delete a stale note block | revise it, so the notes stay with the table |
