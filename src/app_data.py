"""Read-only data access and filtering helpers for the Dash application."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from src.config import PROCESSED_DATA_PATH

REGIONS = ("CISO", "ERCO", "NYIS", "PJM")
RENEWABLE_SOURCES = {
    "solar_mw": "Solar",
    "wind_mw": "Wind",
    "hydro_mw": "Hydropower",
}
GENERATION_SOURCES = {
    "coal_mw": "Coal",
    "natural_gas_mw": "Natural gas",
    "nuclear_mw": "Nuclear",
    "petroleum_mw": "Petroleum",
    "hydro_mw": "Hydropower",
    "solar_mw": "Solar",
    "wind_mw": "Wind",
    "geothermal_mw": "Geothermal",
    "other_mw": "Other",
}
SOURCE_COLORS = {
    "coal_mw": "#5b6573",
    "natural_gas_mw": "#9c6ade",
    "nuclear_mw": "#e4b363",
    "petroleum_mw": "#8c564b",
    "hydro_mw": "#3984b6",
    "solar_mw": "#f3b61f",
    "wind_mw": "#20a486",
    "geothermal_mw": "#d95f59",
    "other_mw": "#9aa5b1",
    "renewables_mw": "#19a974",
}


@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    """Load and lightly index the compact application dataset once per process."""
    frame = pd.read_parquet(PROCESSED_DATA_PATH)
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    frame["data_date"] = pd.to_datetime(frame["data_date"]).dt.normalize()
    frame["local_time_end"] = pd.to_datetime(frame["local_time_end"])
    return frame.sort_values(["balancing_authority", "timestamp_utc"]).reset_index(drop=True)


def available_dates(frame: pd.DataFrame, region: str) -> list[str]:
    subset = frame.loc[frame["balancing_authority"].astype(str) == region, "data_date"]
    return sorted(subset.dt.strftime("%Y-%m-%d").unique().tolist())


def default_date(frame: pd.DataFrame, region: str = "CISO") -> str:
    """Choose a real, complete local day near midsummer."""
    dates = available_dates(frame, region)
    preferred = "2025-06-15"
    return preferred if preferred in dates else dates[len(dates) // 2]


def filter_region(
    frame: pd.DataFrame,
    region: str,
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    mask = frame["balancing_authority"].astype(str).eq(region)
    if start:
        mask &= frame["data_date"].ge(pd.Timestamp(start))
    if end:
        mask &= frame["data_date"].le(pd.Timestamp(end))
    return frame.loc[mask].copy()


def missing_notice(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "No observations match these controls."
    missing = int(frame[columns].isna().sum().sum())
    possible = len(frame) * len(columns)
    return (
        f"{missing:,} of {possible:,} displayed source values are missing and remain gaps."
        if missing
        else "No source values are missing in this selection."
    )
