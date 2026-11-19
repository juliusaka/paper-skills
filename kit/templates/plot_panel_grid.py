#!/usr/bin/env python3
"""TEMPLATE: copy to <generators>/figures/plot_<figure_name>.py and replace the example data."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import numpy as np  # noqa: E402

from paper_kit import style as ps  # noqa: E402

FIGURE_NAME = "example_panel_grid"
CAPTION = "Example signals over time. The dashed lines are the model."

# Panel order and axis labels in one place. Units are plain text.
PANELS = {
    "first": r"$y_1$ (K)",
    "second": r"$y_2$ (W)",
    "third": r"$y_3$ (-)",
}


def main() -> None:
    ps.settings()

    t = np.linspace(0, 3600, 800)
    reference = {name: np.sin(t / 400 + i) for i, name in enumerate(PANELS)}
    model = {name: y + 0.05 * np.cos(t / 90) for name, y in reference.items()}

    fig, axes = ps.figure(width="full", nrows=len(PANELS), sharex=True)
    for ax, (name, label) in zip(axes, PANELS.items()):
        ax.plot(t, reference[name], **ps.role("reference", label="Reference"))
        ax.plot(t, model[name], **ps.role("model", label="Model"))
        ax.set_ylabel(label)
    axes[-1].set_xlabel(r"time $t$ (s)")

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=len(labels))
    fig.align_ylabels(axes)

    ps.save(fig, FIGURE_NAME, caption=CAPTION)


if __name__ == "__main__":
    main()
