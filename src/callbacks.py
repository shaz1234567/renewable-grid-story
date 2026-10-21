"""Dash callback wiring and independently testable interaction helpers."""

from __future__ import annotations

from dash import Input, Output, State, callback, ctx, html

from src.app_data import (
    GENERATION_SOURCES,
    RENEWABLE_SOURCES,
    filter_region,
    missing_notice,
)
from src.figures import (
    generation_mix_figure,
    generation_mix_takeaway,
    portfolio_takeaway,
    regional_comparison_figure,
    regional_takeaway,
    renewable_day_figure,
    renewable_stack_figure,
    source_timeseries_figure,
    variability_figure,
    variability_metrics,
    variability_takeaway,
    cv_comparison_figure,
)


def playback_step(hour: int, direction: int, maximum: int) -> int:
    """Move one observation while clamping at both playback boundaries."""
    return max(0, min(maximum, int(hour or 0) + direction))


def playback_reset(maximum: int) -> int:
    """Reset playback to the first observation."""
    return 0 if maximum >= 0 else 0


def source_selection(trigger: str | None, current: list[str] | None) -> list[str]:
    """Apply portfolio reset without allowing unknown source columns."""
    if trigger == "v6-reset":
        return list(RENEWABLE_SOURCES)
    return [source for source in (current or []) if source in RENEWABLE_SOURCES]


def _metrics_cards(metrics: dict) -> list:
    names = [
        ("Mean", "mean", " MW"),
        ("Minimum", "min", " MW"),
        ("Maximum", "max", " MW"),
        ("Standard deviation", "std", " MW"),
        ("Coefficient of variation", "cv", ""),
    ]
    cards = []
    for label, key, suffix in names:
        value = metrics[key]
        display = "Undefined" if value is None else f"{value:,.2f}{suffix}"
        cards.append(html.Div([html.Span(label), html.Strong(display)], className="metric-card"))
    cards.append(html.Div([html.Span("Missing hours"), html.Strong(f"{metrics['missing']:,}")], className="metric-card"))
    return cards


def register_callbacks(app, frame) -> None:
    @app.callback(
        Output("v1-figure", "figure"),
        Output("v1-notice", "children"),
        Output("v1-takeaway", "children"),
        Input("v1-region", "value"),
        Input("v1-date", "date"),
    )
    def update_mix(region, date):
        subset = filter_region(frame, region, date, date)
        return (
            generation_mix_figure(frame, region, date),
            missing_notice(subset, list(GENERATION_SOURCES)),
            generation_mix_takeaway(frame, region, date),
        )

    @app.callback(
        Output("v2-interval", "disabled"),
        Output("v2-play", "children"),
        Output("v2-play", "aria-pressed"),
        Input("v2-play", "n_clicks"),
        State("v2-interval", "disabled"),
        prevent_initial_call=True,
    )
    def toggle_play(_clicks, disabled):
        now_disabled = not disabled
        return now_disabled, "Play" if now_disabled else "Pause", str(not now_disabled).lower()

    @app.callback(
        Output("v2-hour", "value"),
        Output("v2-hour", "max"),
        Output("v2-hour", "marks"),
        Input("v2-prev", "n_clicks"),
        Input("v2-next", "n_clicks"),
        Input("v2-reset", "n_clicks"),
        Input("v2-interval", "n_intervals"),
        Input("v2-region", "value"),
        Input("v2-date", "date"),
        State("v2-hour", "value"),
    )
    def move_playback(_prev, _next, _reset, _ticks, region, date, hour):
        maximum = max(0, len(filter_region(frame, region, date, date)) - 1)
        trigger = ctx.triggered_id
        if trigger in {"v2-prev"}:
            value = playback_step(hour, -1, maximum)
        elif trigger in {"v2-next", "v2-interval"}:
            value = playback_step(hour, 1, maximum)
        elif trigger == "v2-reset":
            value = playback_reset(maximum)
        elif trigger in {"v2-region", "v2-date"}:
            value = maximum
        else:
            value = min(int(hour or maximum), maximum)
        ticks = sorted(set([0, maximum // 4, maximum // 2, maximum * 3 // 4, maximum]))
        return value, maximum, {tick: str(tick + 1) for tick in ticks}

    @app.callback(
        Output("v2-figure", "figure"),
        Output("v2-notice", "children"),
        Input("v2-region", "value"),
        Input("v2-date", "date"),
        Input("v2-source", "value"),
        Input("v2-hour", "value"),
    )
    def update_day(region, date, source, hour):
        subset = filter_region(frame, region, date, date)
        return renewable_day_figure(frame, region, date, source, hour), missing_notice(subset, [source])

    @app.callback(
        Output("v3-figure", "figure"),
        Output("v3-notice", "children"),
        Input("v3-region", "value"),
        Input("v3-sources", "value"),
        Input("v3-mode", "value"),
    )
    def update_sources(region, sources, mode):
        sources = [source for source in (sources or []) if source in RENEWABLE_SOURCES]
        subset = filter_region(frame, region)
        return source_timeseries_figure(frame, region, sources, mode), missing_notice(subset, sources) if sources else "Select at least one source."

    @app.callback(
        Output("v4-figure", "figure"),
        Output("v4-notice", "children"),
        Output("v4-takeaway", "children"),
        Input("v4-region-a", "value"),
        Input("v4-region-b", "value"),
        Input("v4-source", "value"),
        Input("v4-dates", "start_date"),
        Input("v4-dates", "end_date"),
        Input("v4-mode", "value"),
    )
    def update_regions(region_a, region_b, source, start, end, mode):
        subset = frame[
            frame["balancing_authority"].astype(str).isin([region_a, region_b])
            & frame["data_date"].between(start, end)
        ]
        return (
            regional_comparison_figure(frame, region_a, region_b, source, start, end, mode),
            missing_notice(subset, [source]),
            regional_takeaway(frame, region_a, region_b, source, start, end),
        )

    @app.callback(
        Output("v5-figure", "figure"),
        Output("v5-metrics", "children"),
        Output("v5-notice", "children"),
        Output("v5-takeaway", "children"),
        Input("v5-region", "value"),
        Input("v5-source", "value"),
        Input("v5-dates", "start_date"),
        Input("v5-dates", "end_date"),
    )
    def update_variability(region, source, start, end):
        subset = filter_region(frame, region, start, end)
        metrics = variability_metrics(frame, region, source, start, end)
        return (
            variability_figure(frame, region, source, start, end),
            _metrics_cards(metrics),
            missing_notice(subset, [source]),
            variability_takeaway(frame, region, source, start, end),
        )

    @app.callback(
        Output("v6-sources", "value"),
        Input("v6-reset", "n_clicks"),
        State("v6-sources", "value"),
        prevent_initial_call=True,
    )
    def reset_portfolio(_clicks, current):
        return source_selection(ctx.triggered_id, current)

    @app.callback(
        Output("v6-stack", "figure"),
        Output("v6-cv", "figure"),
        Output("v6-notice", "children"),
        Output("v6-takeaway", "children"),
        Input("v6-region", "value"),
        Input("v6-sources", "value"),
        Input("v6-dates", "start_date"),
        Input("v6-dates", "end_date"),
    )
    def update_portfolio(region, sources, start, end):
        sources = source_selection(None, sources)
        subset = filter_region(frame, region, start, end)
        notice = missing_notice(subset, sources) if sources else "Select at least one source."
        return (
            renewable_stack_figure(frame, region, sources, start, end),
            cv_comparison_figure(frame, region, sources, start, end),
            notice,
            portfolio_takeaway(frame, region, sources, start, end),
        )
