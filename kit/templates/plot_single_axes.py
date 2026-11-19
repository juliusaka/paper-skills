#!/usr/bin/env python3
"""TEMPLATE: copy to <generators>/figures/plot_<figure_name>.py and replace the example data."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # same result over SSH, in a container and in CI

import numpy as np  # noqa: E402

from paper_kit import style as ps  # noqa: E402

FIGURE_NAME = "example_single_axes"
CAPTION = "Example signal over time. The dashed line is the model."


def main() -> None:
    ps.settings()

    t = np.linspace(0, 10, 200)
    reference = np.sin(t)
    model = reference + 0.05 * np.cos(3 * t)

    fig, ax = ps.figure(width="full")
    ax.plot(t, reference, **ps.role("reference", label="Reference"))
    ax.plot(t, model, **ps.role("model", label="Model"))
    ax.set_xlabel(r"time $t$ (s)")
    ax.set_ylabel(r"signal $y$ (-)")
    ax.legend(loc="upper right")

    ps.save(fig, FIGURE_NAME, caption=CAPTION)


if __name__ == "__main__":
    main()
