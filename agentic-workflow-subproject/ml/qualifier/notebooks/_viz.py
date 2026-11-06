"""Shared chart theme for the five journals: one palette, one look, figures exported for the slides.

Every figure is saved twice (SVG for slides, PNG for quick previews) in ``docs/figures/``.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

FIGURES = Path(__file__).resolve().parents[3] / "docs" / "figures"

INK = "#3B2F2A"  # text, dark brown
MUTED = "#8A7A6E"  # secondary text
GRID = "#EDE6DF"
ALERT = (
    "#7A1F1F"  # oxblood: reserved for costly errors (urgent ticket in the wrong desk)
)

# One colour per system, the same in every figure of every journal.
SYSTEM_COLORS = {
    "B0": "#D9CEC3",
    "B1": "#B9A999",
    "B2": "#7A6759",  # the benchmark to beat
    "B3": "#63788A",  # prompted base model
    "D": "#F2B35E",  # fine-tuned, GPU
    "D-q8": "#E8832A",
    "D-q4": "#C2410C",  # the champion
}
NEUTRAL = "#B9A999"
ACCENT = "#C2410C"
SECOND = "#E8A33D"

# One display name per system, the same in every table and figure.
LABELS = {
    "B0": "B0 majority class",
    "B1": "B1 keyword rules",
    "B2": "B2 TF-IDF + logistic regression",
    "B3": "B3 Qwen 3B prompted, not fine-tuned",
    "D": "D Qwen 3B fine-tuned (GPU)",
    "D-q8": "D-q8 fine-tuned, 8-bit (CPU)",
    "D-q4": "D-q4 fine-tuned, 4-bit (CPU)",
}
SILENT = "silent error = valid answer with a wrong desk or reference, not handed to a person"

# Dataset categories (intents) get their own tones so they never read as a system colour.
INTENT_COLORS = {
    "payment_status": "#9C4A1A",
    "dispute": "#D98B3A",
    "technical_api": "#6F8796",
    "compliance": "#5E5048",
    "OTHER": "#CFC3B6",
    "UNDEFINED": "#E9E2DA",
}


def setup() -> None:
    """Apply the theme to matplotlib (call once at the top of each journal)."""
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.family": "sans-serif",
            "font.sans-serif": ["Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "text.color": INK,
            "axes.labelcolor": MUTED,
            "axes.edgecolor": GRID,
            "xtick.color": MUTED,
            "ytick.color": INK,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.spines.left": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "axes.titleweight": "bold",
            "legend.frameon": False,
            "svg.fonttype": "none",
            "figure.dpi": 110,
        }
    )


def headline(fig: Figure, message: str, sub: str = "") -> None:
    """Descriptive figure title plus compact population/units subtitle.

    Call it last: it runs ``tight_layout`` with room reserved for the title block.
    """
    h = fig.get_figheight()
    fig.text(
        0.01,
        1 - 0.1 / h,
        message,
        ha="left",
        va="top",
        fontsize=14,
        fontweight="bold",
        color=INK,
    )
    if sub:
        fig.text(0.01, 1 - 0.42 / h, sub, ha="left", va="top", fontsize=10, color=MUTED)
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.8 / h))


def save(fig: Figure, name: str) -> tuple[Path, Path]:
    """Export and return SVG/PNG paths for slides and MLflow artifact logging."""
    FIGURES.mkdir(parents=True, exist_ok=True)
    svg_path = FIGURES / f"{name}.svg"
    png_path = FIGURES / f"{name}.png"
    fig.savefig(svg_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight", dpi=200)
    return svg_path, png_path


def hbar(
    ax: Axes,
    labels: list[str],
    values: list[float],
    colors: list[str],
    fmt: str = "{:.2f}",
    errors: list[tuple[float, float]] | None = None,
    suffixes: list[str] | None = None,
) -> None:
    """Horizontal bars, first label on top, value written at the end of each bar."""
    ys = list(range(len(labels)))
    ax.barh(ys, values, color=colors, height=0.62)
    if errors:
        for y, v, (lo, hi) in zip(ys, values, errors):
            ax.plot([lo, hi], [y, y], color=INK, lw=1.2)
    top = max(values) if not errors else max(hi for _, hi in errors)
    for i, (y, v) in enumerate(zip(ys, values)):
        end = errors[i][1] if errors else v
        text = fmt.format(v) + (suffixes[i] if suffixes else "")
        ax.text(
            end + top * 0.015,
            y,
            text,
            va="center",
            fontsize=10,
            fontweight="bold",
            color=INK,
        )
    ax.set_yticks(ys, labels)
    ax.invert_yaxis()
    ax.set_xlim(0, top * 1.18)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)


def grouped_hbar(
    ax: Axes,
    groups: list[str],
    series: dict[str, list[float]],
    colors: dict[str, str],
    fmt: str = "{:.1f}",
) -> None:
    """One row per group, one bar per series inside it; missing values (NaN) leave a gap."""
    n = len(series)
    height = 0.8 / n
    top = max(v for vals in series.values() for v in vals if v == v)
    for k, (name, vals) in enumerate(series.items()):
        ys = [g + (k - (n - 1) / 2) * height for g in range(len(groups))]
        ax.barh(ys, vals, height=height * 0.92, color=colors[name], label=name)
        for y, v in zip(ys, vals):
            if v == v:
                ax.text(v + top * 0.012, y, fmt.format(v), va="center", fontsize=8.5, color=INK)
    ax.set_yticks(range(len(groups)), groups)
    ax.invert_yaxis()
    ax.set_xlim(0, top * 1.15)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="y", length=0)
