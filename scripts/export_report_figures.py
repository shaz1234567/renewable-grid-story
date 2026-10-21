"""Export reproducible screenshots of the six default scientific views."""

from pathlib import Path

from src.app_data import load_data
from src.figures import (
    generation_mix_figure,
    regional_comparison_figure,
    renewable_day_figure,
    renewable_stack_figure,
    source_timeseries_figure,
    variability_figure,
)


OUTPUT_DIR = Path("report/screenshots")
WIDTH = 1400
HEIGHT = 760


def main() -> None:
    frame = load_data()
    renewable_sources = ["solar_mw", "wind_mw", "hydro_mw"]
    figures = {
        "view-1-generation-mix.png": generation_mix_figure(
            frame, "CISO", "2025-06-15"
        ),
        "view-2-hourly-rhythm.png": renewable_day_figure(
            frame, "CISO", "2025-06-15", "solar_mw", 23
        ),
        "view-3-source-comparison.png": source_timeseries_figure(
            frame, "CISO", renewable_sources
        ),
        "view-4-regional-comparison.png": regional_comparison_figure(
            frame,
            "CISO",
            "ERCO",
            "solar_mw",
            "2025-01-01",
            "2025-12-31",
        ),
        "view-5-variability.png": variability_figure(
            frame, "CISO", "solar_mw", "2025-01-01", "2025-12-31"
        ),
        "view-6-portfolio.png": renewable_stack_figure(
            frame,
            "CISO",
            renewable_sources,
            "2025-01-01",
            "2025-12-31",
        ),
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, figure in figures.items():
        figure.write_image(
            OUTPUT_DIR / filename,
            width=WIDTH,
            height=HEIGHT,
            scale=1.5,
        )
        print(OUTPUT_DIR / filename)


if __name__ == "__main__":
    main()
