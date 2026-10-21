"""Compute reproducible summary metrics from prepared EIA-930 data."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

from src.config import METRICS_PATH, PROCESSED_DATA_PATH, YEAR

ENERGY_COLUMNS = [
    "coal_mw",
    "natural_gas_mw",
    "nuclear_mw",
    "petroleum_mw",
    "geothermal_mw",
    "other_mw",
    "unknown_mw",
    "solar_mw",
    "wind_mw",
    "hydro_mw",
    "renewables_mw",
    "generation_mix_mw",
    "net_generation_mw",
]


def _energy_metrics(frame: pd.DataFrame) -> dict[str, float | None]:
    # EIA-930 observations are one-hour averages, so summed MW equals interval MWh.
    mwh = {}
    for column in ENERGY_COLUMNS:
        value = float(frame[column].sum(min_count=1))
        mwh[column.removesuffix("_mw") + "_mwh"] = (
            round(value, 3) if math.isfinite(value) else None
        )
    denominator = mwh["net_generation_mwh"]
    peak = float(frame["renewables_mw"].max())
    mean = float(frame["renewables_mw"].mean())
    return {
        **mwh,
        "renewable_share_of_net_generation_pct": (
            round(100 * mwh["renewables_mwh"] / denominator, 3)
            if denominator and denominator > 0
            else None
        ),
        "peak_renewables_mw": round(peak, 3) if math.isfinite(peak) else None,
        "mean_renewables_mw": round(mean, 3) if math.isfinite(mean) else None,
    }


def compute_metrics(
    input_path: Path = PROCESSED_DATA_PATH,
    output_path: Path = METRICS_PATH,
) -> dict:
    data = pd.read_parquet(input_path)
    data["timestamp_utc"] = pd.to_datetime(data["timestamp_utc"], utc=True)

    by_authority = {
        authority: _energy_metrics(group)
        for authority, group in data.groupby("balancing_authority", observed=True)
    }
    monthly = {}
    month_key = data["data_date"].dt.to_period("M").astype(str)
    for (authority, month), group in data.groupby(
        ["balancing_authority", month_key], observed=True
    ):
        monthly.setdefault(authority, {})[month] = _energy_metrics(group)

    metrics = {
        "year": YEAR,
        "interval_hours": 1,
        "energy_unit": "MWh",
        "methodology": (
            "Energy is the sum of hourly average MW. Primary renewables include solar and "
            "wind both with and without integrated battery storage, plus hydropower excluding "
            "pumped storage. The primary generation mix also includes coal, natural gas, "
            "nuclear, petroleum, geothermal, other, and unknown fuels; standalone and pumped "
            "storage are excluded."
        ),
        "by_balancing_authority": by_authority,
        "monthly_by_balancing_authority": monthly,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n")
    return metrics


if __name__ == "__main__":
    result = compute_metrics()
    print(json.dumps(result["by_balancing_authority"], indent=2))
