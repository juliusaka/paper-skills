"""One look for every figure: measured sizes, role colours and a reproducible save."""

from __future__ import annotations

import os
import warnings
from pathlib import Path

import matplotlib
import numpy as np
from cycler import cycler
from matplotlib.font_manager import FontProperties

from . import config as config_module
from . import fit, regen

PT_PER_INCH = 72.27  # TeX points, not PostScript points
HALF_WIDTH_FRACTION = 0.49  # two subfigures side by side, the rest is the gutter
GOLDEN_RATIO = 1.6180339887
PANEL_HEIGHT_IN = 0.95
PANEL_MARGIN_IN = 0.70
PNG_DPI = 300

# Okabe-Ito palette, safe for colour-blind readers.
CB_COLORS = ["#E69F00", "#56B4E9", "#009E73", "#0072B2", "#D55E00", "#CC79A7", "#F0E442"]

# Colour and line style change together, so series stay apart in greyscale.
line_cycler = cycler(color=CB_COLORS) + cycler(linestyle=["-", "--", "-.", ":", "-", "--", "-."])

ROLE_STYLES = {
    "reference": {"color": "#0072B2", "linestyle": "-"},
    "model": {"color": "#D55E00", "linestyle": "--"},
    "setpoint": {"color": "#009E73", "linestyle": ":"},
    "baseline": {"color": "#CC79A7", "linestyle": "-."},
    "limit": {"color": "#B2182B", "linestyle": (0, (3, 1))},
}

# For a quantity defined everywhere on the axes.
CMAP = matplotlib.colormaps["plasma"]


def _white_anchored(name: str, base: str, head: float = 0.06):
    colors = matplotlib.colormaps[base](np.linspace(0.0, 1.0, 256))[:, :3]
    fade = np.linspace(0.0, 1.0, int(head * 256))[:, None]
    ramp = (1.0 - fade) + fade * colors[0]
    return matplotlib.colors.LinearSegmentedColormap.from_list(name, np.vstack([ramp, colors]))


# For counts and densities: an empty cell is white, and lightness falls monotonically.
DENSITY_CMAP = _white_anchored("paper_density", "magma_r").with_extremes(under="#FFFFFF", bad="#FFFFFF")

RC_PARAMS = {
    "font.family": "serif",
    "font.serif": ["Nimbus Roman", "Liberation Serif", "Times New Roman", "DejaVu Serif"],
    "font.size": 7,
    "mathtext.fontset": "stix",
    "svg.fonttype": "path",  # outlines: no font lookup when the paper is built
    "svg.hashsalt": "paper-kit",  # stable ids: a rerun does not change the file
    "pdf.fonttype": 42,
    "lines.linewidth": 0.6,
    "lines.markersize": 4,
    "lines.markeredgewidth": 1.0,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "grid.linewidth": 0.4,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.prop_cycle": line_cycler,
    "legend.frameon": False,
    "figure.dpi": 150,
    "savefig.dpi": 300,
}


# Text sizes relative to font.size, so one setting scales all of them.
_SIZE_OFFSETS = {
    "axes.titlesize": 1,
    "axes.labelsize": 0,
    "legend.fontsize": 0,
    "xtick.labelsize": -1,
    "ytick.labelsize": -1,
}


def role(name: str, **overrides) -> dict:
    """Plot arguments for a line that means something, for example ``role("model", label="Ours")``."""
    if name not in ROLE_STYLES:
        raise KeyError(f"unknown role {name!r}; known roles: {sorted(ROLE_STYLES)}")
    return {**ROLE_STYLES[name], **overrides}


def settings(**overrides) -> None:
    """Apply the style. Project overrides come from ``[style]`` in paper_kit.toml."""
    chosen = {**config_module.load().rc_overrides, **overrides}
    params = {**RC_PARAMS, **chosen}
    for key, offset in _SIZE_OFFSETS.items():
        params.setdefault(key, params["font.size"] + offset)
    matplotlib.rcParams.update(params)


def _page_inches() -> dict[str, float]:
    page = config_module.load().page
    return {key: page[f"{key}_pt"] / PT_PER_INCH for key in ("textwidth", "columnwidth", "textheight")}


def across(n: int) -> float:
    """On-page width in inches of one of ``n`` equal figures on a row."""
    return _page_inches()["textwidth"] / n


def resolve_width(width: str | float = "full") -> float:
    """On-page width in inches: "full", "column", "half" or a number of inches."""
    page = _page_inches()
    named = {
        "full": page["textwidth"],
        "column": page["columnwidth"],
        "half": page["columnwidth"] * HALF_WIDTH_FRACTION,
    }
    if isinstance(width, str):
        if width not in named:
            raise ValueError(f"width must be one of {sorted(named)} or a number, got {width!r}")
        return named[width]
    if width > page["textwidth"]:
        warnings.warn(f"width {width:.3f} in is wider than the text block", stacklevel=2)
    return float(width)


def figure(width: str | float = "full", height: float | None = None, *, nrows: int = 1, ncols: int = 1, **kwargs):
    """``plt.subplots`` at the size the figure has on the page, so LaTeX scales it by 1."""
    import matplotlib.pyplot as plt

    width_in = resolve_width(width)
    if height is None:
        height = PANEL_HEIGHT_IN * nrows + PANEL_MARGIN_IN if nrows > 1 else width_in / GOLDEN_RATIO
    kwargs.setdefault("layout", "constrained")
    return plt.subplots(nrows, ncols, figsize=(width_in, height), **kwargs)


def _include_line(config: config_module.Config, target: Path, width: float, page: dict[str, float]) -> str:
    """The LaTeX command that includes this figure at scale 1."""
    widths = {
        r"\textwidth": page["textwidth"],
        r"\columnwidth": page["columnwidth"],
        rf"{HALF_WIDTH_FRACTION}\columnwidth": page["columnwidth"] * HALF_WIDTH_FRACTION,
    }
    expression = next((tex for tex, inches in widths.items() if abs(inches - width) < 0.005), f"{width:.3f}in")
    command = "includesvg" if config.figure_formats[0] == "svg" else "includegraphics"
    path = Path(os.path.relpath(target, config.tex.parent)).as_posix()
    wide = width > page["columnwidth"] * 1.01
    return f"  include{' in figure*' if wide else ''}: \\{command}[width={expression}]{{{path}}}"


def save(fig, name: str, *, caption: str | None = None, placement: str = fit.DEFAULT_SPECIFIER, **savefig_kwargs) -> list[Path]:
    """Write the figure and its regeneration script, and report its page fit for ``caption``.

    ``placement`` is the float specifier the paper uses for this figure.
    """
    config = config_module.load()
    target = config.figures_dir / name
    target.parent.mkdir(parents=True, exist_ok=True)
    savefig_kwargs["bbox_inches"] = None  # trimming would change the on-page size
    metadata = {"svg": {"Date": None}, "pdf": {"CreationDate": None}}

    written, changed = [], False
    for file_type in config.figure_formats:
        path = target.with_name(f"{target.name}.{file_type}")
        before = path.read_bytes() if path.exists() else None
        kwargs = dict(savefig_kwargs)
        if file_type in metadata:
            kwargs.setdefault("metadata", metadata[file_type])
        if file_type == "png":
            kwargs.setdefault("dpi", PNG_DPI)
        fig.savefig(path, **kwargs)
        changed = changed or path.read_bytes() != before
        written.append(path)
    script = regen.write_script(target, config.root, written, changed)
    if script is not None:
        written.append(script)

    for path in written:
        print(os.path.relpath(path, config.root))
    width, height = (float(value) for value in fig.get_size_inches())
    page = _page_inches()
    label_pt = FontProperties(size=matplotlib.rcParams["axes.labelsize"]).get_size_in_points()
    print(
        f"  {width:.3f} x {height:.3f} in on the page ({width / page['textwidth']:.3f} textwidth), "
        f"labels {label_pt:.2f} pt"
    )
    print(_include_line(config, target, width, page))
    if height > page["textheight"]:
        print(f"  WARNING: taller than the {page['textheight']:.2f} in text block")
    if caption is None:
        print("  page fit not measured: pass the planned caption to save()")
        return written

    environment = "figure*" if width > page["columnwidth"] * 1.01 else "figure"
    fragment = (
        rf"\begin{{{environment}}}[{placement}]\centering\rule{{{width}in}}{{{height}in}}"
        rf"\caption{{{caption}}}\end{{{environment}}}"
    )
    result = fit.measure(config, name, fragment)
    if result is not None:
        result.report()
    return written
