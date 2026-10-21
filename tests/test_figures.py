import pandas as pd

from src.figures import (
    SOURCE_COLORS,
    cv_comparison_figure,
    generation_mix_figure,
    portfolio_takeaway,
    regional_comparison_figure,
    region_map_figure,
    renewable_day_figure,
    renewable_stack_figure,
    source_timeseries_figure,
    variability_figure,
    variability_metrics,
)


def sample_frame():
    rows = []
    for region, multiplier in [("CISO", 1.0), ("ERCO", 2.0)]:
        for hour in range(48):
            timestamp = pd.Timestamp("2025-06-15", tz="UTC") + pd.Timedelta(hours=hour)
            solar = [0.0, 10.0, 20.0, 0.0][hour % 4] * multiplier
            wind = (8 + hour % 3) * multiplier
            hydro = 5 * multiplier
            rows.append(
                {
                    "balancing_authority": region,
                    "data_date": timestamp.tz_localize(None).normalize(),
                    "timestamp_utc": timestamp,
                    "local_time_end": timestamp.tz_localize(None),
                    "solar_mw": solar,
                    "wind_mw": wind,
                    "hydro_mw": hydro,
                    "renewables_mw": solar + wind + hydro,
                    "coal_mw": 4.0,
                    "natural_gas_mw": 12.0,
                    "nuclear_mw": 6.0,
                    "petroleum_mw": 0.0,
                    "geothermal_mw": None,
                    "other_mw": 1.0,
                }
            )
    return pd.DataFrame(rows)


def test_generation_mix_builds_stacked_source_traces():
    figure = generation_mix_figure(sample_frame(), "CISO", "2025-06-15")
    assert len(figure.data) >= 5
    assert all(trace.stackgroup == "mix" for trace in figure.data)
    assert "MW" in figure.layout.yaxis.title.text
    assert figure.layout.margin.t >= 118
    assert figure.layout.legend.yanchor == "bottom"
    assert figure.layout.legend.entrywidthmode == "pixels"


def test_empty_data_returns_annotated_figure():
    figure = generation_mix_figure(sample_frame().iloc[0:0], "CISO", "2025-06-15")
    assert not figure.data
    assert "No data" in figure.layout.annotations[0].text


def test_source_toggle_limits_traces_and_normalizes():
    figure = source_timeseries_figure(sample_frame(), "CISO", ["wind_mw"], "normalized")
    assert [trace.name for trace in figure.data] == ["Wind"]
    assert max(figure.data[0].y) == 100


def test_renewable_palette_is_colorblind_safe_and_consistent_across_builders():
    frame = sample_frame()
    profiles = source_timeseries_figure(
        frame, "CISO", ["solar_mw", "wind_mw", "hydro_mw"]
    )
    stack = renewable_stack_figure(
        frame, "CISO", ["solar_mw", "wind_mw", "hydro_mw"]
    )
    expected = [
        SOURCE_COLORS["solar_mw"],
        SOURCE_COLORS["wind_mw"],
        SOURCE_COLORS["hydro_mw"],
    ]
    assert [trace.line.color for trace in profiles.data] == expected
    assert [trace.line.color for trace in stack.data[:3]] == expected
    assert len(set(expected)) == 3


def test_regional_comparison_uses_same_dates_and_separate_normalization():
    figure = regional_comparison_figure(
        sample_frame(), "CISO", "ERCO", "wind_mw", "2025-06-15", "2025-06-16", "normalized"
    )
    assert {trace.name for trace in figure.data} == {"CISO", "ERCO"}
    assert all(max(trace.y) == 100 for trace in figure.data)
    assert list(figure.data[0].x) == list(figure.data[1].x)
    assert [trace.line.dash for trace in figure.data] == ["solid", "dash"]


def test_regional_comparison_uses_selected_source():
    frame = sample_frame()
    solar = regional_comparison_figure(
        frame, "CISO", "ERCO", "solar_mw", "2025-06-15", "2025-06-15"
    )
    wind = regional_comparison_figure(
        frame, "CISO", "ERCO", "wind_mw", "2025-06-15", "2025-06-15"
    )
    assert solar.data[0].y[0] != wind.data[0].y[0]
    assert "solar" in solar.layout.title.text.lower()


def test_variability_cv_is_safe_for_zero_mean():
    frame = sample_frame()
    frame.loc[frame["balancing_authority"] == "CISO", "solar_mw"] = 0.0
    metrics = variability_metrics(frame, "CISO", "solar_mw")
    assert metrics["cv"] is None
    assert metrics["mean"] == 0


def test_variability_metrics_respect_date_range():
    metrics = variability_metrics(
        sample_frame(), "CISO", "solar_mw", "2025-06-15", "2025-06-15"
    )
    assert metrics["max"] == 20
    assert metrics["mean"] == 7.5


def test_portfolio_toggle_adds_combined_total():
    figure = renewable_stack_figure(sample_frame(), "CISO", ["solar_mw", "wind_mw"])
    assert [trace.name for trace in figure.data] == ["Solar", "Wind", "Combined selected total"]


def test_portfolio_figures_and_takeaway_respect_date_range():
    frame = sample_frame()
    stack = renewable_stack_figure(
        frame, "CISO", ["solar_mw", "wind_mw"], "2025-06-16", "2025-06-16"
    )
    cv = cv_comparison_figure(
        frame, "CISO", ["solar_mw", "wind_mw"], "2025-06-16", "2025-06-16"
    )
    takeaway = portfolio_takeaway(
        frame, "CISO", ["solar_mw", "wind_mw"], "2025-06-16", "2025-06-16"
    )
    assert set(stack.data[0].x) == {pd.Timestamp("2025-06-16")}
    assert len(cv.data) == 1
    assert "2025-06-16 to 2025-06-16" in takeaway


def test_all_remaining_figure_builders_share_readable_layout():
    frame = sample_frame()
    figures = [
        renewable_day_figure(frame, "CISO", "2025-06-15", "solar_mw"),
        variability_figure(frame, "CISO", "wind_mw"),
        cv_comparison_figure(frame, "CISO", ["solar_mw", "wind_mw"]),
    ]
    for figure in figures:
        assert figure.layout.title.font.size == 20
        assert figure.layout.margin.t >= 118
        assert figure.layout.yaxis.automargin
        assert figure.layout.yaxis.tickformat == "~s"
        assert figure.layout.hoverlabel.bgcolor == "#FFFFFF"


def test_map_title_is_wrapped_and_has_dedicated_margin():
    figure = region_map_figure(sample_frame())
    assert "<br>" in figure.layout.title.text
    assert figure.layout.margin.t >= 78
    assert figure.layout.showlegend is False
