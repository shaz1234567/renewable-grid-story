"""Layout factory for the six-view renewable-grid story."""

from __future__ import annotations

from dash import dcc, html

from src.app_data import REGIONS, RENEWABLE_SOURCES, default_date
from src.figures import (
    cv_comparison_figure,
    generation_mix_takeaway,
    generation_mix_figure,
    portfolio_takeaway,
    region_map_figure,
    regional_comparison_figure,
    regional_takeaway,
    renewable_day_figure,
    renewable_stack_figure,
    source_timeseries_figure,
    variability_figure,
    variability_metrics,
    variability_takeaway,
)

GRAPH_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}
SOURCE_OPTIONS = [{"label": label, "value": key} for key, label in RENEWABLE_SOURCES.items()]
REGION_OPTIONS = [{"label": region, "value": region} for region in REGIONS]


def _graph(graph_id: str, figure) -> dcc.Graph:
    return dcc.Graph(id=graph_id, figure=figure, config=GRAPH_CONFIG, className="story-graph")


def _control(label: str, component) -> html.Div:
    return html.Div([html.Label(label), component], className="control")


def _section(number: str, title: str, eyebrow: str, children: list) -> html.Section:
    return html.Section(
        [
            html.Div(
                [
                    html.Span(number, className="view-number", **{"aria-hidden": "true"}),
                    html.Div([html.P(eyebrow, className="eyebrow"), html.H2(title, id=f"view-{number}-title")]),
                ],
                className="section-heading",
            ),
            *children,
        ],
        id=f"view-{number}",
        className="story-section",
        **{"aria-labelledby": f"view-{number}-title"},
    )


def _metrics_cards(metrics: dict) -> html.Div:
    def value(name: str, suffix: str = "") -> str:
        raw = metrics[name]
        return "Undefined" if raw is None else f"{raw:,.2f}{suffix}"

    cards = [
        ("Mean", value("mean", " MW")),
        ("Minimum", value("min", " MW")),
        ("Maximum", value("max", " MW")),
        ("Standard deviation", value("std", " MW")),
        ("Coefficient of variation", value("cv")),
        ("Missing hours", f"{metrics['missing']:,}"),
    ]
    return html.Div(
        [html.Div([html.Span(label), html.Strong(display)], className="metric-card") for label, display in cards],
        id="v5-metrics",
        className="metrics-grid",
        **{"aria-live": "polite"},
    )


def create_layout(frame):
    date = default_date(frame)
    start, end = "2025-01-01", "2025-12-31"
    metrics = variability_metrics(frame, "CISO", "solar_mw", start, end)
    nav = html.Nav(
        [
            html.A("Grid in motion", href="#top", className="brand"),
            html.Div(
                [html.A(f"{i} · {name}", href=f"#view-{i}") for i, name in enumerate(
                    ["Mix", "A day", "Seasons", "Regions", "Variability", "Portfolio"], start=1
                )],
                className="nav-links",
            ),
        ],
        className="site-nav",
        **{"aria-label": "Story sections"},
    )
    hero = html.Header(
        [
            html.P("EIA-930 · four balancing authorities · 2025", className="eyebrow"),
            html.H1("The renewable grid, hour by hour"),
            html.P(
                "An interactive scientific story about how solar, wind, and hydropower move "
                "through a day, across a year, and between U.S. power regions.",
                className="dek",
            ),
            html.P("Scroll to explore ↓", className="scroll-cue"),
        ],
        id="top",
        className="hero",
    )

    view1 = _section("1", "What powers an ordinary day?", "The daily mix", [
        html.P("Generation sources rise and recede together. Choose a region and operating day; the stack retains reported negative values and gaps.", className="intro"),
        html.Div([
            _control("Balancing authority", dcc.Dropdown(REGION_OPTIONS, "CISO", id="v1-region", clearable=False)),
            _control("Operating date", dcc.DatePickerSingle(id="v1-date", date=date, min_date_allowed="2025-01-01", max_date_allowed="2025-12-31")),
        ], className="controls"),
        html.Div([_graph("v1-figure", generation_mix_figure(frame, "CISO", date)), html.Aside(
            generation_mix_takeaway(frame, "CISO", date),
            id="v1-takeaway", className="takeaway", **{"aria-live": "polite"},
        )], className="chart-card"),
        html.P(id="v1-notice", className="data-notice", **{"aria-live": "polite"}),
    ])

    playback = html.Div([
        html.Button("Previous", id="v2-prev", n_clicks=0),
        html.Button("Play", id="v2-play", n_clicks=0, **{"aria-pressed": "false"}),
        html.Button("Next", id="v2-next", n_clicks=0),
        html.Button("Reset", id="v2-reset", n_clicks=0, className="button-secondary"),
    ], className="button-row")
    view2 = _section("2", "Watch renewables build a day", "Hourly rhythm", [
        html.P("Advance one observation at a time. On daylight-saving transition days, the source may contain 23 or 25 local-hour observations.", className="intro"),
        html.Div([
            _control("Balancing authority", dcc.Dropdown(REGION_OPTIONS, "CISO", id="v2-region", clearable=False)),
            _control("Operating date", dcc.DatePickerSingle(id="v2-date", date=date, min_date_allowed="2025-01-01", max_date_allowed="2025-12-31")),
            _control("Renewable source", dcc.Dropdown(SOURCE_OPTIONS, "solar_mw", id="v2-source", clearable=False)),
        ], className="controls"),
        playback,
        dcc.Slider(0, 23, 1, value=23, id="v2-hour", marks={0: "1", 5: "6", 11: "12", 17: "18", 23: "24"}, tooltip={"placement": "bottom"}),
        dcc.Interval(id="v2-interval", interval=700, disabled=True, n_intervals=0),
        _graph("v2-figure", renewable_day_figure(frame, "CISO", date, "solar_mw")),
        html.P(id="v2-notice", className="data-notice", **{"aria-live": "polite"}),
    ])

    view3 = _section("3", "Seasons reshape every source", "The annual pulse", [
        html.P("Daily means expose seasonal structure without drawing 8,760 points. Normalized mode scales each source to its own annual peak.", className="intro"),
        html.Div([
            _control("Balancing authority", dcc.Dropdown(REGION_OPTIONS, "CISO", id="v3-region", clearable=False)),
            _control("Sources", dcc.Checklist(SOURCE_OPTIONS, list(RENEWABLE_SOURCES), id="v3-sources", inline=True)),
            _control("Scale", dcc.RadioItems([{"label": "Absolute", "value": "absolute"}, {"label": "Normalized", "value": "normalized"}], "absolute", id="v3-mode", inline=True)),
        ], className="controls"),
        _graph("v3-figure", source_timeseries_figure(frame, "CISO", list(RENEWABLE_SOURCES))),
        html.P(id="v3-notice", className="data-notice", **{"aria-live": "polite"}),
    ])

    view4 = _section("4", "Place changes the renewable profile", "Regional context", [
        html.P("Points are schematic reference locations—not balancing-authority boundaries. Compare two regions over exactly the same operating dates.", className="intro"),
        html.Div([_graph("v4-map", region_map_figure(frame)), html.Div([
            html.Div([
                _control("Region A", dcc.Dropdown(REGION_OPTIONS, "CISO", id="v4-region-a", clearable=False)),
                _control("Region B", dcc.Dropdown(REGION_OPTIONS, "ERCO", id="v4-region-b", clearable=False)),
                _control("Renewable source", dcc.Dropdown(SOURCE_OPTIONS, "solar_mw", id="v4-source", clearable=False)),
                _control("Period", dcc.DatePickerRange(id="v4-dates", start_date="2025-01-01", end_date="2025-12-31", min_date_allowed="2025-01-01", max_date_allowed="2025-12-31")),
                _control("Scale", dcc.RadioItems([{"label": "Raw MW", "value": "absolute"}, {"label": "Normalized", "value": "normalized"}], "absolute", id="v4-mode", inline=True)),
            ], className="controls"),
            _graph("v4-figure", regional_comparison_figure(frame, "CISO", "ERCO", "solar_mw", start, end)),
            html.Aside(regional_takeaway(frame, "CISO", "ERCO", "solar_mw", start, end), id="v4-takeaway", className="takeaway", **{"aria-live": "polite"}),
            html.P(id="v4-notice", className="data-notice", **{"aria-live": "polite"}),
        ])], className="two-column"),
    ])

    view5 = _section("5", "Variability is measurable", "Beyond the average", [
        html.P("Hourly observations reveal spread, extremes, and missingness. CV is σ / |μ| and is reported as undefined when the mean is zero or unavailable.", className="intro"),
        html.Div([
            _control("Balancing authority", dcc.Dropdown(REGION_OPTIONS, "CISO", id="v5-region", clearable=False)),
            _control("Source", dcc.Dropdown(SOURCE_OPTIONS, "solar_mw", id="v5-source", clearable=False)),
            _control("Period", dcc.DatePickerRange(id="v5-dates", start_date=start, end_date=end, min_date_allowed=start, max_date_allowed=end)),
        ], className="controls"),
        _metrics_cards(metrics),
        _graph("v5-figure", variability_figure(frame, "CISO", "solar_mw", start, end)),
        html.Aside(variability_takeaway(frame, "CISO", "solar_mw", start, end), id="v5-takeaway", className="takeaway", **{"aria-live": "polite"}),
        html.P(id="v5-notice", className="data-notice", **{"aria-live": "polite"}),
    ])

    view6 = _section("6", "A portfolio can smooth the signal", "Complementarity", [
        html.P("Stack selected renewables and compare each source’s CV with their combined hourly portfolio. Lower CV indicates less variation relative to the mean.", className="intro"),
        html.Div([
            _control("Balancing authority", dcc.Dropdown(REGION_OPTIONS, "CISO", id="v6-region", clearable=False)),
            _control("Portfolio sources", dcc.Checklist(SOURCE_OPTIONS, list(RENEWABLE_SOURCES), id="v6-sources", inline=True)),
            _control("Period", dcc.DatePickerRange(id="v6-dates", start_date=start, end_date=end, min_date_allowed=start, max_date_allowed=end)),
            html.Button("Reset sources", id="v6-reset", n_clicks=0, className="button-secondary"),
        ], className="controls"),
        html.Div([
            _graph("v6-stack", renewable_stack_figure(frame, "CISO", list(RENEWABLE_SOURCES), start, end)),
            _graph("v6-cv", cv_comparison_figure(frame, "CISO", list(RENEWABLE_SOURCES), start, end)),
        ], className="two-column"),
        html.Aside(portfolio_takeaway(frame, "CISO", list(RENEWABLE_SOURCES), start, end), id="v6-takeaway", className="takeaway", **{"aria-live": "polite"}),
        html.P(id="v6-notice", className="data-notice", **{"aria-live": "polite"}),
    ])

    footer = html.Footer([
        html.P("Source: U.S. EIA-930 hourly balancing-authority operations, 2025."),
        html.P("Values are reported hourly average MW; daily curves show arithmetic daily means. This is an explanatory visualization, not an operational forecast."),
    ])
    return html.Div([nav, html.Main([hero, view1, view2, view3, view4, view5, view6]), footer])
