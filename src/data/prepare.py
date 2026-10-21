"""Prepare compact hourly fuel-mix data from EIA-930 archives."""

import argparse
import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from src.config import (
    ARCHIVES,
    BALANCING_AUTHORITIES,
    DATA_QUALITY_PATH,
    PROCESSED_DATA_PATH,
    RAW_DATA_DIR,
    YEAR,
)

RAW_FIELDS = {
    "demand_mw": "Demand (MW)",
    "net_generation_mw": "Net Generation (MW)",
    "coal_mw": "Net Generation (MW) from Coal",
    "natural_gas_mw": "Net Generation (MW) from Natural Gas",
    "nuclear_mw": "Net Generation (MW) from Nuclear",
    "petroleum_mw": "Net Generation (MW) from All Petroleum Products",
    "hydro_mw": "Net Generation (MW) from Hydropower Excluding Pumped Storage",
    "solar_without_battery_mw": (
        "Net Generation (MW) from Solar without Integrated Battery Storage"
    ),
    "solar_with_battery_mw": (
        "Net Generation (MW) from Solar with Integrated Battery Storage"
    ),
    "wind_without_battery_mw": (
        "Net Generation (MW) from Wind without Integrated Battery Storage"
    ),
    "wind_with_battery_mw": (
        "Net Generation (MW) from Wind with Integrated Battery Storage"
    ),
    "geothermal_mw": "Net Generation (MW) from Geothermal",
    "other_mw": "Net Generation (MW) from Other Fuel Sources",
    "unknown_mw": "Net Generation (MW) from Unknown Fuel Sources",
}

PRIMARY_GENERATION_COLUMNS = [
    "coal_mw",
    "natural_gas_mw",
    "nuclear_mw",
    "petroleum_mw",
    "hydro_mw",
    "solar_mw",
    "wind_mw",
    "geothermal_mw",
    "other_mw",
    "unknown_mw",
]

# The source itself misspells "with" as "witho" only in this adjusted column.
ADJUSTED_OVERRIDES = {
    "solar_with_battery_mw": (
        "Net Generation (MW) from Solar witho Integrated Battery Storage (Adjusted)"
    )
}


def _variants(output_name: str, raw_name: str) -> tuple[str, str, str]:
    adjusted = ADJUSTED_OVERRIDES.get(output_name, f"{raw_name} (Adjusted)")
    return adjusted, f"{raw_name} (Imputed)", raw_name


INPUT_COLUMNS = [
    "Balancing Authority",
    "Data Date",
    "Hour Number",
    "Local Time at End of Hour",
    "UTC Time at End of Hour",
    "Region",
    *dict.fromkeys(
        column
        for output_name, raw_name in RAW_FIELDS.items()
        for column in _variants(output_name, raw_name)
    ),
]


def _preferred_series(frame: pd.DataFrame, output_name: str, raw_name: str) -> pd.Series:
    adjusted, imputed, raw = _variants(output_name, raw_name)
    return (
        pd.to_numeric(frame[adjusted], errors="coerce")
        .combine_first(pd.to_numeric(frame[imputed], errors="coerce"))
        .combine_first(pd.to_numeric(frame[raw], errors="coerce"))
    )


def _read_balance(path: Path) -> pd.DataFrame:
    with ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.endswith("-balance.csv")]
        if len(members) != 1:
            raise ValueError(f"Expected one balance CSV in {path}, found {members}")
        with archive.open(members[0]) as stream:
            return pd.read_csv(
                stream,
                usecols=INPUT_COLUMNS,
                dtype={"Balancing Authority": "string", "Region": "string"},
                low_memory=False,
            )


def prepare_data(
    raw_dir: Path = RAW_DATA_DIR,
    output_path: Path = PROCESSED_DATA_PATH,
) -> tuple[pd.DataFrame, dict]:
    """Prepare the four requested balancing authorities and write parquet + DQ JSON."""
    source_frames = []
    source_rows = {}
    for filename in ARCHIVES:
        frame = _read_balance(raw_dir / filename)
        source_rows[filename] = int(len(frame))
        frame["source_archive"] = filename
        source_frames.append(frame)

    raw = pd.concat(source_frames, ignore_index=True)
    filtered = raw[raw["Balancing Authority"].isin(BALANCING_AUTHORITIES)].copy()

    output = pd.DataFrame(
        {
            "balancing_authority": filtered["Balancing Authority"],
            "data_date": pd.to_datetime(filtered["Data Date"], format="%m/%d/%Y"),
            "timestamp_utc": pd.to_datetime(
                filtered["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p", utc=True
            ),
            "local_time_end": pd.to_datetime(
                filtered["Local Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p"
            ),
            "region": filtered["Region"],
            "source_archive": filtered["source_archive"],
        }
    )
    for output_name, raw_name in RAW_FIELDS.items():
        output[output_name] = _preferred_series(filtered, output_name, raw_name)

    # A missing integrated-storage component means that the BA did not report that
    # category. Treat it as zero only for aggregation and retain the nullable component.
    output["solar_mw"] = output[
        ["solar_without_battery_mw", "solar_with_battery_mw"]
    ].sum(axis=1, min_count=1)
    output["wind_mw"] = output[
        ["wind_without_battery_mw", "wind_with_battery_mw"]
    ].sum(axis=1, min_count=1)
    output["renewables_mw"] = output[["solar_mw", "wind_mw", "hydro_mw"]].sum(
        axis=1, min_count=1
    )
    output["generation_mix_mw"] = output[PRIMARY_GENERATION_COLUMNS].sum(
        axis=1, min_count=1
    )

    output = output.sort_values(["balancing_authority", "timestamp_utc"]).reset_index(drop=True)
    numeric_columns = output.select_dtypes(include="number").columns
    output[numeric_columns] = output[numeric_columns].astype("float32")
    output["balancing_authority"] = output["balancing_authority"].astype("category")
    output["region"] = output["region"].astype("category")
    output["source_archive"] = output["source_archive"].astype("category")

    expected_hours = 365 * 24
    coverage = {}
    for authority, group in output.groupby("balancing_authority", observed=True):
        coverage[str(authority)] = {
            "rows": int(len(group)),
            "expected_hours": expected_hours,
            "coverage_pct": round(100 * len(group) / expected_hours, 3),
            "first_timestamp_utc": group["timestamp_utc"].min().isoformat(),
            "last_timestamp_utc": group["timestamp_utc"].max().isoformat(),
        }

    quality = {
        "year": YEAR,
        "source_rows": source_rows,
        "filtered_rows": int(len(output)),
        "balancing_authorities": sorted(output["balancing_authority"].astype(str).unique()),
        "duplicate_authority_timestamps": int(
            output.duplicated(["balancing_authority", "timestamp_utc"]).sum()
        ),
        "null_counts": {key: int(value) for key, value in output.isna().sum().items()},
        "coverage": coverage,
        "output_columns": list(output.columns),
        "primary_generation_columns": PRIMARY_GENERATION_COLUMNS,
        "generation_mix_exclusions": [
            "pumped storage",
            "standalone battery storage",
            "other energy storage",
            "unknown energy storage",
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output.to_parquet(output_path, index=False, compression="zstd")
    DATA_QUALITY_PATH.write_text(json.dumps(quality, indent=2) + "\n")
    return output, quality


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR)
    parser.add_argument("--output", type=Path, default=PROCESSED_DATA_PATH)
    args = parser.parse_args()
    _, quality = prepare_data(args.raw_dir, args.output)
    print(json.dumps(quality, indent=2))


if __name__ == "__main__":
    main()
