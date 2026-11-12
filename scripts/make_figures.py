"""Draw the README charts from the tables SPSS exported to results/.

    python scripts/make_figures.py

Every chart is saved twice, for light and dark backgrounds. Titles state the
finding, take their numbers from the result files, and are guarded by checks,
so a chart cannot claim something the data does not show.

Rules followed: one message and one axis per chart, one colour when the marks
measure the same thing, thin marks, hairline gridlines, an interval line on
every estimate, and numbers printed at the marks.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"

THEMES = {
    "light": {"surface": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "muted": "#898781",
              "grid": "#e1e0d9", "axis": "#c3c2b7", "blue": "#2a78d6"},
    "dark": {"surface": "#1a1a19", "ink": "#f0efec", "ink2": "#c3c2b7", "muted": "#898781",
             "grid": "#2c2c2a", "axis": "#383835", "blue": "#3987e5"},
}
SOURCE = "Data: Afrobarometer Round 10, Nigeria, 2024 (1,600 adults), afrobarometer.org.  Analysis: Elisha Abraham."
DPI = 200
WIDTH = 7.2
OUTCOME = "Went without medicines or medical treatment several times or more in the past year"
WHO = ("Adults who say they or someone in their family went without medicines or medical treatment\n"
       "several times or more in the past year. Lines show 95% confidence intervals.")

_installed = {font.name for font in font_manager.fontManager.ttflist}
plt.rcParams["font.family"] = next(
    (name for name in ("Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans") if name in _installed), "sans-serif")


# ---------------------------------------------------------------- reading SPSS tables

def table(name: str) -> list[dict]:
    """One exported SPSS table. SPSS writes an empty cell as a single space."""
    with (RESULTS / f"{name}.csv").open(newline="", encoding="utf-8-sig") as handle:
        return [{key: value.strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def group_rates(name: str, group: str, outcome: str) -> dict[str, dict]:
    """Percentage answering Yes in each level of `group`, from a two-way table: {level: estimate, low, high}."""
    rates: dict[str, dict] = {}
    for row in table(name):
        if row["Label_"] != f"{group} * {outcome}":
            continue
        key = {("Estimate", ""): "estimate", ("95% Confidence Interval", "Lower"): "low",
               ("95% Confidence Interval", "Upper"): "high"}.get((row["Var3"], row["Var4"]))
        if key:
            rates.setdefault(row["Var1"], {})[key] = float(row["Yes"])
    return rates


def yes_rates(name: str) -> dict[str, dict]:
    """Percentage answering Yes for each variable in a one-way table: {variable label: estimate, low, high}."""
    return {row["Label_"]: {"estimate": float(row["Estimate"]), "low": float(row["Lower"]), "high": float(row["Upper"])}
            for row in table(name) if row["Var2"] == "Yes"}


# ---------------------------------------------------------------- building blocks

def _figure(theme: dict, title: str, subtitle: str, height: float):
    fig = plt.figure(figsize=(WIDTH, height), dpi=DPI)
    fig.patch.set_facecolor(theme["surface"])
    top = 1 - 0.19 / height
    fig.text(0.04, top, title, fontsize=12.5, fontweight="semibold", color=theme["ink"], ha="left", va="top")
    fig.text(0.04, top - 0.30 / height, subtitle, fontsize=9, color=theme["ink2"], ha="left", va="top")
    fig.text(0.04, 0.10 / height, SOURCE, fontsize=6.8, color=theme["muted"], ha="left", va="bottom")
    return fig


def _axes(fig, theme: dict, box: list[float]):
    ax = fig.add_axes(box)
    ax.set_facecolor(theme["surface"])
    for side in ("top", "right", "bottom"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(theme["axis"])
    ax.spines["left"].set_linewidth(0.8)
    ax.grid(axis="x", color=theme["grid"], linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", length=0, labelsize=9, colors=theme["muted"], pad=5)
    ax.tick_params(axis="y", length=0, labelsize=9, colors=theme["ink2"], pad=6)
    return ax


def _per_pixel(ax) -> tuple[float, float]:
    """Data units covered by one logical pixel (1/100 inch) on each axis."""
    ax.figure.canvas.draw()
    scale = ax.figure.dpi / 100
    (x0, y0), (x1, y1) = ax.transData.inverted().transform([(0, 0), (scale, scale)])
    return abs(x1 - x0), abs(y1 - y0)


def _save(fig, name: str, theme_name: str) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{name}_{theme_name}.png", dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)


def interval_bars(rows: list[dict], title: str, subtitle: str, name: str, x_max: float, ticks: list[int],
                  label_width: float = 0.33) -> None:
    """Horizontal bars for percentages with 95% interval lines.
    rows: dicts with label, estimate, low, high. A row with estimate None is a group heading."""
    extra = 0.17 * subtitle.count("\n")  # room for a second subtitle line
    height = 1.55 + extra + 0.34 * len(rows)
    for theme_name, theme in THEMES.items():
        fig = _figure(theme, title, subtitle, height)
        ax = _axes(fig, theme, [label_width, 0.52 / height, 0.96 - label_width, 1 - (1.40 + extra) / height])
        ax.set_xlim(0, x_max)
        ax.set_ylim(len(rows) - 0.4, -0.6)
        ax.set_xticks(ticks, [f"{tick}%" if tick else "0" for tick in ticks])
        ax.set_yticks(range(len(rows)), [row["label"] for row in rows])
        dx, dy = _per_pixel(ax)
        for y, (row, tick) in enumerate(zip(rows, ax.get_yticklabels())):
            if row.get("estimate") is None:
                tick.set_color(theme["ink"])
                tick.set_fontweight("semibold")
                continue
            thickness, radius = 14 * dy, 4
            ax.add_patch(FancyBboxPatch((0, y - thickness / 2), row["estimate"], thickness,
                                        boxstyle=f"round,pad=0,rounding_size={radius * dx}", mutation_aspect=dy / dx,
                                        facecolor=theme["blue"], edgecolor="none", zorder=3))
            ax.add_patch(Rectangle((0, y - thickness / 2), max(row["estimate"] - radius * dx, 0), thickness,
                                   facecolor=theme["blue"], edgecolor="none", zorder=3))
            ax.hlines(y, row["low"], row["high"], color=theme["ink2"], linewidth=1, zorder=4)
            ax.text(row["high"] + 6 * dx, y, f"{row['estimate']:.1f}%", fontsize=9, color=theme["ink"], ha="left", va="center")
        _save(fig, name, theme_name)


def forest(rows: list[dict], title: str, subtitle: str, name: str, x_ticks: list[float]) -> None:
    """Odds ratios with 95% intervals on a log axis. A row with odds_ratio None is a group heading;
    a row with reference=True is the comparison group, drawn at 1."""
    extra = 0.17 * subtitle.count("\n")  # room for a second subtitle line
    height = 1.87 + extra + 0.30 * len(rows)
    for theme_name, theme in THEMES.items():
        fig = _figure(theme, title, subtitle, height)
        ax = _axes(fig, theme, [0.40, 0.84 / height, 0.40, 1 - (1.72 + extra) / height])  # room below for the axis title
        ax.spines["left"].set_visible(False)
        ax.set_xscale("log")
        ax.set_xlim(x_ticks[0] * 0.8, x_ticks[-1] * 1.25)  # room beyond the end ticks for long intervals
        ax.set_ylim(len(rows) - 0.4, -0.6)
        ax.set_xticks(x_ticks, [f"{tick:g}" for tick in x_ticks])
        ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
        ax.set_yticks(range(len(rows)), [row["label"] for row in rows])
        ax.axvline(1, color=theme["ink2"], linewidth=0.8, zorder=2)
        for y, (row, tick) in enumerate(zip(rows, ax.get_yticklabels())):
            if row.get("odds_ratio") is None and not row.get("reference"):
                tick.set_color(theme["ink"])
                tick.set_fontweight("semibold")
                continue
            if row.get("reference"):
                ax.plot(1, y, "o", markersize=6, markerfacecolor=theme["surface"], markeredgecolor=theme["ink2"],
                        markeredgewidth=1.2, zorder=4)
                label = "1.00  (comparison)"
            else:
                ax.hlines(y, row["low"], row["high"], color=theme["ink2"], linewidth=1, zorder=3)
                ax.plot(row["odds_ratio"], y, "o", markersize=7.5, color=theme["blue"], markeredgecolor=theme["surface"],
                        markeredgewidth=1.5, zorder=4)
                label = f"{row['odds_ratio']:.2f}  ({row['low']:.2f} to {row['high']:.2f})"
            ax.text(1.04, y, label, transform=ax.get_yaxis_transform(), fontsize=9, color=theme["ink"], ha="left", va="center")
        ax.set_xlabel("Adjusted odds ratio (log scale)", fontsize=9, color=theme["ink2"], labelpad=6)
        _save(fig, name, theme_name)


# ---------------------------------------------------------------- the four charts

def by_zone() -> None:
    zones = group_rates("without_care_by_group", "Geopolitical zone", OUTCOME)
    everyone = zones.pop("Total")
    ordered = sorted(zones.items(), key=lambda item: -item[1]["estimate"])
    (top_name, top), (bottom_name, bottom) = ordered[0], ordered[-1]
    assert top["low"] > bottom["high"]  # the title contrasts the two ends: their intervals must not overlap
    rows = [{"label": "Nigeria", **everyone}] + [{"label": name, **rate} for name, rate in ordered]
    interval_bars(rows, f"{top_name}: {top['estimate']:.0f}% went without medical care. {bottom_name}: {bottom['estimate']:.0f}%",
                  WHO, "01_without_care_by_zone", x_max=96, ticks=[0, 20, 40, 60, 80], label_width=0.19)


def by_group() -> None:
    def block(heading: str, group: str, relabel: dict[str, str] | None = None) -> list[dict]:
        rates = group_rates("without_care_by_group", group, OUTCOME)
        rates.pop("Total")
        return [{"label": heading, "estimate": None}] + [{"label": (relabel or {}).get(name, name), **rate}
                                                         for name, rate in rates.items()]

    deprivation = block("Household deprivation", "Deprivation level",
                        {"Low (0 to 1)": "Low", "Moderate (above 1 to 2)": "Moderate", "High (above 2)": "High"})
    sex = block("Sex", "Woman")
    assert deprivation[3]["estimate"] - deprivation[1]["estimate"] > 50  # deprivation separates people sharply
    assert abs(sex[1]["estimate"] - sex[2]["estimate"]) < 5              # sex does not
    rows = (deprivation + block("Health clinic in the area", "Health clinic in the enumeration area",
                                {"No clinic in the area": "No clinic", "Clinic in the area": "Clinic"})
            + block("Where they live", "Rural enumeration area") + block("Education", "Education") + sex)
    interval_bars(rows, "Poverty and place decide who goes without care. Sex does not",
                  WHO, "02_without_care_by_group", x_max=108, ticks=[0, 20, 40, 60, 80, 100], label_width=0.27)


def odds_ratios() -> None:
    estimates = {row["Var2"]: row for row in table("model2_estimates")}

    def line(label: str, parameter: str) -> dict:
        row = estimates[parameter]
        return {"label": label, "odds_ratio": float(row["ExpB"]), "low": float(row["Lower_A"]), "high": float(row["Upper_A"])}

    def heading(text: str) -> dict:
        return {"label": text, "odds_ratio": None}

    north = [line("North East", "[zone=2]"), line("North West", "[zone=3]"), line("North Central", "[zone=1]")]
    assert all(row["low"] > 1 for row in north)  # the title says the north stands out after adjustment
    rows = ([heading("Household deprivation"), line("One point higher on the index", "deprivation"),
             heading("Zone")] + north + [line("South South", "[zone=5]"), line("South East", "[zone=4]"),
                                         {"label": "South West", "reference": True},
             heading("Place"), line("Rural (against urban)", "rural"), line("No clinic in the area", "no_clinic"),
             heading("Person"), line("Has medical aid cover", "insured"), line("Woman (against man)", "female"),
             line("Ten years older", "age_decades"),
             heading("Education"), line("No formal schooling", "[education=1]"), line("Primary", "[education=2]"),
             line("Secondary", "[education=3]"), {"label": "Post-secondary", "reference": True}])
    forest(rows, "At the same level of deprivation, the north still goes without more",
           "Odds that the respondent or their family went without medicines or medical treatment several times\n"
           "or more. Each factor is adjusted for all the others; lines show 95% confidence intervals.",
           "03_adjusted_odds_ratios", x_ticks=[0.25, 0.5, 1, 2, 4, 8])


def clinic_experience() -> None:
    rates = yes_rates("clinic_experience")
    users = next(row["UnweightedCount"] for row in table("headline")
                 if row["Label_"] == "Had contact with a public clinic or hospital in the past year" and row["Var2"] == "Yes")
    difficult = rates["Found it difficult or very difficult to get the care needed"]
    bribe = rates["Paid a bribe, gave a gift or did a favour to get care, at least once"]
    problems = [("Long waiting time", "Long waiting time, a few times or often"),
                ("High cost prevented care or medicines", "High cost prevented care or medicines, a few times or often"),
                ("Poor condition of facilities", "Poor condition of facilities, a few times or often"),
                ("Lack of medicines or supplies", "Lack of medicines or supplies, a few times or often"),
                ("Absence of doctors or other staff", "Absence of doctors or other staff, a few times or often")]
    rows = ([{"label": "Getting care", "estimate": None},
             {"label": "Found it difficult or very difficult", **difficult},
             {"label": "Paid a bribe, gave a gift or did a favour", **bribe},
             {"label": "Met a few times or often", "estimate": None}]
            + sorted(({"label": label, **rates[key]} for label, key in problems), key=lambda row: -row["estimate"]))
    interval_bars(rows, f"{difficult['estimate']:.0f}% of public clinic users found care hard to get; "
                        f"{bribe['estimate']:.0f}% paid a bribe or gift",
                  f"Adults who had contact with a public clinic or hospital in the past year ({users} respondents).\n"
                  "Lines show 95% confidence intervals.",
                  "04_clinic_experience", x_max=82, ticks=[0, 20, 40, 60], label_width=0.37)


def main() -> None:
    for draw in (by_zone, by_group, odds_ratios, clinic_experience):
        draw()
    for path in sorted(FIGURES.glob("*.png")):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
