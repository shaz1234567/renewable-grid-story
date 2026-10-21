"""Pure, testable Plotly figure builders."""

from __future__ import annotations

import math
import textwrap

import pandas as pd
import plotly.graph_objects as go

from src.app_data import (
    GENERATION_SOURCES,
    RENEWABLE_SOURCES,
    filter_region,
)

EMPTY_MESSAGE = "No data are available for this selection."

# Okabe-Ito hues identify renewables; quieter tones keep contextual fuels secondary.
SOURCE_COLORS = {
    "solar_mw": "#E69F00",
    "wind_mw": "#009E73",
    "hydro_mw": "#0072B2",
    "coal_mw": "#4B5563",
    "natural_gas_mw": "#7C8798",
    "nuclear_mw": "#B5A06A",
    "petroleum_mw": "#8B6F67",
    "geothermal_mw": "#9A7A85",
    "other_mw": "#CBD5E1",
    "renewables_mw": "#009E73",
}
REGION_COLORS = ("#0072B2", "#D55E00")
BASE_LAYOUT = {
    "template": "plotly_white",
    "font": {"family": "Inter, system-ui, sans-serif", "color": "#18302b"},
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(255,255,255,.7)",
    "margin": {"l": 62, "r": 24, "t": 74, "b": 112},
    "hovermode": "x unified",
    "hoverlabel": {
        "bgcolor": "#FFFFFF",
        "bordercolor": "#CEDBD5",
        "font": {"family": "Inter, system-ui, sans-serif", "color": "#18302b", "size": 12},
    },
    "legend": {
        "orientation": "h",
        "x": 0,
        "xanchor": "left",
        "y": 0.02,
        "yanchor": "bottom",
        "yref": "container",
        "font": {"size": 12},
        "traceorder": "normal",
        "entrywidth": 72,
        "entrywidthmode": "pixels",
    },
}


def empty_figure(message: str = EMPTY_MESSAGE) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(**BASE_LAYOUT)
    fig.update_layout(showlegend=False, margin={"l": 24, "r": 24, "t": 48, "b": 36})
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def _title_text(title: str) -> str:
    """Wrap long titles at word boundaries for narrow responsive containers."""
    return "<br>".join(textwrap.wrap(title, width=36, break_long_words=False))


def _finish(fig: go.Figure, title: str, y_title: str, x_title: str = "Time") -> go.Figure:
    # Reserve a bottom band for the x axis plus horizontal legend rows. Using
    # container coordinates keeps the legend out of the title zone at every width.
    legend_rows = math.ceil(len(fig.data) / 2)
    bottom_margin = max(112, 74 + legend_rows * 22)
    layout = {
        **BASE_LAYOUT,
        "margin": {"l": 62, "r": 24, "t": 74, "b": bottom_margin},
    }
    fig.update_layout(
        **layout,
        title={
            "text": _title_text(title),
            "x": 0,
            "xanchor": "left",
            "y": 0.98,
            "yanchor": "top",
            "font": {"size": 20, "color": "#18302b"},
        },
    )
    fig.update_xaxes(
        title=x_title,
        showgrid=False,
        showline=True,
        linecolor="#CEDBD5",
        ticks="outside",
        tickcolor="#A9BBB4",
        automargin=True,
        hoverformat="%Y-%m-%d",
    )
    fig.update_yaxes(
        title=y_title,
        rangemode="tozero",
        gridcolor="#E2EAE7",
        gridwidth=1,
        zeroline=False,
        tickformat="~s",
        separatethousands=True,
        automargin=True,
    )
    return fig


def generation_mix_figure(frame: pd.DataFrame, region: str, date: str) -> go.Figure:
    day = filter_region(frame, region, date, date)
    if day.empty:
        return empty_figure()
    fig = go.Figure()
    for column, label in GENERATION_SOURCES.items():
        values = day[column]
        if values.notna().any() and values.fillna(0).abs().sum() > 0:
            fig.add_trace(
                go.Scatter(
                    x=day["local_time_end"],
                    y=values,
                    name=label,
                    mode="lines",
                    stackgroup="mix",
                    line={"width": 0.6, "color": SOURCE_COLORS[column]},
                    opacity=0.9 if column in RENEWABLE_SOURCES else 0.72,
                    hovertemplate=f"{label}: %{{y:,.0f}} MW<extra></extra>",
                )
            )
    return _finish(fig, f"{region} generation mix · {date}", "Hourly average generation (MW)", "Local time at end of hour")


def renewable_day_figure(
    frame: pd.DataFrame, region: str, date: str, source: str, hour: int = 23
) -> go.Figure:
    day = filter_region(frame, region, date, date).iloc[: max(0, hour) + 1]
    if day.empty or source not in RENEWABLE_SOURCES:
        return empty_figure()
    label = RENEWABLE_SOURCES[source]
    fig = go.Figure(
        go.Scatter(
            x=day["local_time_end"],
            y=day[source],
            name=label,
            mode="lines+markers",
            line={"width": 3, "color": SOURCE_COLORS[source]},
            marker={"size": 5, "line": {"color": "white", "width": 0.75}},
            hovertemplate=f"%{{x|%H:%M}} · {label}: %{{y:,.0f}} MW<extra></extra>",
        )
    )
    return _finish(fig, f"{label} through hour {min(hour + 1, len(day))}", "Hourly average generation (MW)", "Local time at end of hour")


def source_timeseries_figure(
    frame: pd.DataFrame,
    region: str,
    sources: list[str],
    mode: str = "absolute",
) -> go.Figure:
    subset = filter_region(frame, region)
    valid = [source for source in sources if source in RENEWABLE_SOURCES]
    if subset.empty or not valid:
        return empty_figure("Select at least one renewable source.")
    daily = subset.set_index("data_date")[valid].resample("D").mean()
    fig = go.Figure()
    for source in valid:
        values = daily[source]
        label = RENEWABLE_SOURCES[source]
        if mode == "normalized":
            maximum = values.abs().max()
            values = values / maximum * 100 if maximum and math.isfinite(maximum) else values * math.nan
            hover = f"{label}: %{{y:.2f}}% of annual peak<extra></extra>"
        else:
            hover = f"{label}: %{{y:,.2f}} MW daily mean<extra></extra>"
        fig.add_trace(
            go.Scatter(
                x=daily.index,
                y=values,
                name=label,
                line={"width": 2.25, "color": SOURCE_COLORS[source]},
                hovertemplate="%{x|%Y-%m-%d} · " + hover,
            )
        )
    unit = "Percent of each source's annual peak (%)" if mode == "normalized" else "Daily mean generation (MW)"
    return _finish(fig, f"{region} renewable source profiles", unit, "Date (local operating day)")


REGION_POINTS = {
    "CISO": (-119.7, 36.7),
    "ERCO": (-99.3, 31.0),
    "NYIS": (-75.5, 42.9),
    "PJM": (-79.6, 39.4),
}


def region_map_figure(frame: pd.DataFrame) -> go.Figure:
    means = frame.groupby("balancing_authority", observed=True)["renewables_mw"].mean()
    fig = go.Figure()
    for region, (lon, lat) in REGION_POINTS.items():
        value = float(means.get(region, math.nan))
        fig.add_trace(
            go.Scattergeo(
                lon=[lon],
                lat=[lat],
                text=[f"{region}<br>Annual mean renewables: {value:,.0f} MW"],
                name=region,
                mode="markers+text",
                textposition="top center",
                marker={"size": 14, "color": "#147d64", "line": {"color": "white", "width": 2}},
                hovertemplate="%{text}<extra></extra>",
            )
        )
    layout = {
        **BASE_LAYOUT,
        "title": {
            "text": _title_text("Approximate balancing-authority reference points"),
            "x": 0,
            "xanchor": "left",
            "y": 0.94,
            "yanchor": "top",
            "font": {"size": 20, "color": "#18302b"},
        },
        "geo": {
            "scope": "usa",
            "projection": {"type": "albers usa"},
            "showland": True,
            "landcolor": "#edf4f1",
            "showlakes": True,
            "lakecolor": "#dceef2",
            "subunitcolor": "#c7d8d2",
        },
        "showlegend": False,
        "margin": {"l": 12, "r": 12, "t": 78, "b": 8},
    }
    fig.update_layout(**layout)
    return fig


def regional_comparison_figure(
    frame: pd.DataFrame,
    region_a: str,
    region_b: str,
    source: str,
    start: str,
    end: str,
    mode: str = "absolute",
) -> go.Figure:
    if source not in RENEWABLE_SOURCES:
        return empty_figure("Choose a renewable source.")
    subset = frame[
        frame["balancing_authority"].astype(str).isin([region_a, region_b])
        & frame["data_date"].between(pd.Timestamp(start), pd.Timestamp(end))
    ]
    if subset.empty:
        return empty_figure()
    daily = (
        subset.groupby(["data_date", "balancing_authority"], observed=True)[source]
        .mean()
        .unstack()
    )
    fig = go.Figure()
    for index, region in enumerate(dict.fromkeys([region_a, region_b])):
        if region not in daily:
            continue
        values = daily[region]
        if mode == "normalized":
            maximum = values.abs().max()
            values = values / maximum * 100 if maximum else values * math.nan
            hover = "%{y:.2f}% of period peak"
        else:
            hover = "%{y:,.2f} MW daily mean"
        fig.add_trace(
            go.Scatter(
                x=daily.index,
                y=values,
                name=region,
                mode="lines",
                line={
                    "width": 2.25,
                    "color": REGION_COLORS[index % len(REGION_COLORS)],
                    "dash": "solid" if index == 0 else "dash",
                },
                hovertemplate="%{x|%Y-%m-%d} · " + hover + "<extra></extra>",
            )
        )
    label = RENEWABLE_SOURCES[source]
    unit = "Percent of each region's period peak (%)" if mode == "normalized" else f"Daily mean {label.lower()} generation (MW)"
    return _finish(fig, f"{region_a} and {region_b}: {label.lower()} comparison", unit, "Date (local operating day)")


def variability_metrics(
    frame: pd.DataFrame,
    region: str,
    source: str,
    start: str | None = None,
    end: str | None = None,
) -> dict[str, float | int | None]:
    subset = filter_region(frame, region, start, end)
    values = subset[source].dropna() if source in subset else pd.Series(dtype=float)
    if values.empty:
        return {"mean": None, "min": None, "max": None, "std": None, "cv": None, "missing": len(subset)}
    mean = float(values.mean())
    std = float(values.std())
    return {
        "mean": mean,
        "min": float(values.min()),
        "max": float(values.max()),
        "std": std,
        "cv": std / abs(mean) if math.isfinite(mean) and abs(mean) > 1e-12 else None,
        "missing": int(subset[source].isna().sum()),
    }


def variability_figure(
    frame: pd.DataFrame,
    region: str,
    source: str,
    start: str | None = None,
    end: str | None = None,
) -> go.Figure:
    if source not in RENEWABLE_SOURCES:
        return empty_figure()
    subset = filter_region(frame, region, start, end)
    if subset.empty:
        return empty_figure()
    label = RENEWABLE_SOURCES[source]
    fig = go.Figure(
        go.Scattergl(
            x=subset["timestamp_utc"],
            y=subset[source],
            name=label,
            line={"width": 1.4, "color": SOURCE_COLORS[source]},
            hovertemplate="%{x|%Y-%m-%d %H:%M UTC} · %{y:,.0f} MW<extra></extra>",
        )
    )
    return _finish(fig, f"{region} hourly {label.lower()} variability", "Hourly average generation (MW)", "Timestamp (UTC)")


def renewable_stack_figure(
    frame: pd.DataFrame,
    region: str,
    sources: list[str],
    start: str | None = None,
    end: str | None = None,
) -> go.Figure:
    valid = [source for source in sources if source in RENEWABLE_SOURCES]
    subset = filter_region(frame, region, start, end)
    if subset.empty or not valid:
        return empty_figure("Select at least one renewable source.")
    daily = subset.set_index("data_date")[valid].resample("D").mean()
    fig = go.Figure()
    for source in valid:
        label = RENEWABLE_SOURCES[source]
        fig.add_trace(
            go.Scatter(
                x=daily.index,
                y=daily[source],
                name=label,
                stackgroup="renewables",
                line={"width": 0.6, "color": SOURCE_COLORS[source]},
                opacity=0.86,
                hovertemplate=f"{label}: %{{y:,.2f}} MW<extra></extra>",
            )
        )
    total = daily.sum(axis=1, min_count=1)
    fig.add_trace(
        go.Scatter(
            x=daily.index,
            y=total,
            name="Combined selected total",
            mode="lines",
            line={"width": 2.5, "color": "#102a43"},
            hovertemplate="Combined: %{y:,.2f} MW<extra></extra>",
        )
    )
    return _finish(fig, f"{region} renewable portfolio", "Daily mean generation (MW)", "Date (local operating day)")


def cv_comparison_figure(
    frame: pd.DataFrame,
    region: str,
    sources: list[str],
    start: str | None = None,
    end: str | None = None,
) -> go.Figure:
    valid = [source for source in sources if source in RENEWABLE_SOURCES]
    if not valid:
        return empty_figure("Select at least one renewable source.")
    labels, values, colors = [], [], []
    for source in valid:
        metrics = variability_metrics(frame, region, source, start, end)
        if metrics["cv"] is not None:
            labels.append(RENEWABLE_SOURCES[source])
            values.append(metrics["cv"])
            colors.append(SOURCE_COLORS[source])
    selected = filter_region(frame, region, start, end)
    combined = selected[valid].sum(axis=1, min_count=1)
    mean, std = combined.mean(), combined.std()
    if pd.notna(mean) and abs(mean) > 1e-12:
        labels.append("Combined selected")
        values.append(float(std / abs(mean)))
        colors.append("#102a43")
    if not values:
        return empty_figure("Coefficient of variation is undefined for this selection.")
    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker_color=colors,
            hovertemplate="%{x}: CV %{y:.4f}<extra></extra>",
        )
    )
    return _finish(fig, "Relative variability: lower CV is steadier", "Coefficient of variation (σ / |μ|)", "Portfolio")


def generation_mix_takeaway(frame: pd.DataFrame, region: str, date: str) -> str:
    """Summarize the largest reported source for one selected day."""
    subset = filter_region(frame, region, date, date)
    totals = subset[list(GENERATION_SOURCES)].sum(min_count=1).dropna()
    if totals.empty:
        return "Takeaway: the selected day has too little reported data for a source comparison."
    source = totals.idxmax()
    share_denominator = totals.clip(lower=0).sum()
    share = 100 * max(float(totals[source]), 0) / share_denominator if share_denominator > 0 else math.nan
    share_text = f", about {share:.1f}% of the positive reported mix" if math.isfinite(share) else ""
    return (
        f"Takeaway: {GENERATION_SOURCES[source]} has the largest summed hourly average in "
        f"{region} on {date}{share_text}. This describes reported generation, not causal dispatch."
    )


def regional_takeaway(
    frame: pd.DataFrame,
    region_a: str,
    region_b: str,
    source: str,
    start: str,
    end: str,
) -> str:
    """Compare selected-period source means without implying significance."""
    label = RENEWABLE_SOURCES.get(source, "Selected source")
    means = {
        region: filter_region(frame, region, start, end)[source].mean()
        for region in dict.fromkeys([region_a, region_b])
        if source in frame
    }
    if len(means) < 2 or any(pd.isna(value) for value in means.values()):
        return "Takeaway: the selected period has insufficient reported data for a two-region comparison."
    first, second = means[region_a], means[region_b]
    if math.isclose(float(first), float(second), rel_tol=0.001, abs_tol=0.01):
        relation = "have nearly equal reported hourly means"
    else:
        higher = region_a if first > second else region_b
        lower = region_b if first > second else region_a
        ratio = max(first, second) / min(first, second) if min(first, second) > 0 else math.nan
        relation = (
            f"has a higher reported hourly mean than {lower}"
            + (f" (about {ratio:.2f}×)" if math.isfinite(ratio) else "")
        )
        relation = f"{higher} {relation}"
    return f"Takeaway: for {label.lower()} from {start} to {end}, {relation}. This is a descriptive comparison."


def variability_takeaway(
    frame: pd.DataFrame,
    region: str,
    source: str,
    start: str,
    end: str,
) -> str:
    metrics = variability_metrics(frame, region, source, start, end)
    label = RENEWABLE_SOURCES.get(source, "selected source")
    if metrics["cv"] is None:
        return (
            f"Takeaway: {label} CV is undefined for {region} in this period because its "
            "reported mean is zero or unavailable."
        )
    return (
        f"Takeaway: {region} {label.lower()} averages {metrics['mean']:,.1f} MW with a "
        f"CV of {metrics['cv']:.3f} from {start} to {end}. CV describes relative spread, not predictability."
    )


def portfolio_takeaway(
    frame: pd.DataFrame,
    region: str,
    sources: list[str],
    start: str,
    end: str,
) -> str:
    valid = [source for source in sources if source in RENEWABLE_SOURCES]
    selected = filter_region(frame, region, start, end)
    if selected.empty or not valid:
        return "Takeaway: select at least one source with reported data to assess portfolio variability."
    individual = {
        source: variability_metrics(frame, region, source, start, end)["cv"] for source in valid
    }
    individual = {source: value for source, value in individual.items() if value is not None}
    combined = selected[valid].sum(axis=1, min_count=1)
    mean = combined.mean()
    combined_cv = combined.std() / abs(mean) if pd.notna(mean) and abs(mean) > 1e-12 else math.nan
    if not individual or not math.isfinite(combined_cv):
        return "Takeaway: CV is undefined for the selected portfolio because usable means are zero or unavailable."
    lowest_source = min(individual, key=individual.get)
    lowest_cv = individual[lowest_source]
    comparison = (
        f"below the lowest selected individual CV ({lowest_cv:.3f})"
        if combined_cv < lowest_cv
        else f"not below the lowest selected individual CV ({lowest_cv:.3f})"
    )
    return (
        f"Takeaway: {region}’s selected portfolio CV is {combined_cv:.3f}, {comparison}, "
        f"from {start} to {end}. This is descriptive and depends on the chosen sources and period."
    )
