"""Validate raw provenance and the prepared 2025 EIA-930 dataset."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.config import (
    ARCHIVES,
    BALANCING_AUTHORITIES,
    PROCESSED_DATA_PATH,
    RAW_DATA_DIR,
    RAW_MANIFEST_PATH,
    VALIDATION_PATH,
    YEAR,
    ZENODO_RECORD_ID,
    ZENODO_RECORD_VERSION,
)
from src.data.download_eia930 import file_hash
from src.data.prepare import PRIMARY_GENERATION_COLUMNS


def _check(name: str, passed: bool, detail: object) -> dict:
    return {"name": name, "passed": bool(passed), "detail": detail}


def validate_data(
    input_path: Path = PROCESSED_DATA_PATH,
    manifest_path: Path = RAW_MANIFEST_PATH,
    output_path: Path = VALIDATION_PATH,
) -> dict:
    data = pd.read_parquet(input_path)
    manifest = json.loads(manifest_path.read_text())
    data["timestamp_utc"] = pd.to_datetime(data["timestamp_utc"], utc=True)
    data["data_date"] = pd.to_datetime(data["data_date"])

    checks = []
    actual_authorities = sorted(data["balancing_authority"].dropna().unique().tolist())
    checks.append(
        _check(
            "balancing_authorities",
            actual_authorities == sorted(BALANCING_AUTHORITIES),
            actual_authorities,
        )
    )
    rows_by_authority = data.groupby("balancing_authority", observed=True).size().to_dict()
    checks.append(
        _check(
            "8760_hourly_rows_per_authority",
            all(rows_by_authority.get(authority) == 8760 for authority in BALANCING_AUTHORITIES),
            {key: int(value) for key, value in rows_by_authority.items()},
        )
    )
    duplicate_count = int(
        data.duplicated(["balancing_authority", "timestamp_utc"], keep=False).sum()
    )
    checks.append(_check("unique_ba_timestamp", duplicate_count == 0, duplicate_count))

    gap_counts = {}
    for authority, group in data.groupby("balancing_authority", observed=True):
        ordered = group["timestamp_utc"].sort_values()
        gap_counts[authority] = int((ordered.diff().dropna() != pd.Timedelta(hours=1)).sum())
    checks.append(
        _check("continuous_hourly_utc", not any(gap_counts.values()), gap_counts)
    )
    observed_years = sorted(data["data_date"].dt.year.unique().tolist())
    date_range = [
        data["data_date"].min().date().isoformat(),
        data["data_date"].max().date().isoformat(),
    ]
    checks.append(
        _check(
            "complete_2025_data_dates",
            observed_years == [YEAR] and date_range == ["2025-01-01", "2025-12-31"],
            {"years": observed_years, "range": date_range},
        )
    )

    required_non_null = [
        "demand_mw",
        "net_generation_mw",
        "renewables_mw",
        "generation_mix_mw",
    ]
    null_counts = {column: int(data[column].isna().sum()) for column in required_non_null}
    checks.append(_check("required_values_present", not any(null_counts.values()), null_counts))

    recomputed = data[
        [
            "solar_without_battery_mw",
            "solar_with_battery_mw",
        ]
    ].sum(axis=1, min_count=1)
    solar_mismatches = int(
        (~(data["solar_mw"].eq(recomputed) | (data["solar_mw"].isna() & recomputed.isna()))).sum()
    )
    recomputed = data[
        ["wind_without_battery_mw", "wind_with_battery_mw"]
    ].sum(axis=1, min_count=1)
    wind_mismatches = int(
        (~(data["wind_mw"].eq(recomputed) | (data["wind_mw"].isna() & recomputed.isna()))).sum()
    )
    recomputed = data[["solar_mw", "wind_mw", "hydro_mw"]].sum(axis=1, min_count=1)
    renewable_mismatches = int(
        (~(
            data["renewables_mw"].eq(recomputed)
            | (data["renewables_mw"].isna() & recomputed.isna())
        )).sum()
    )
    checks.append(
        _check(
            "renewable_category_arithmetic",
            solar_mismatches == wind_mismatches == renewable_mismatches == 0,
            {
                "solar_mismatches": solar_mismatches,
                "wind_mismatches": wind_mismatches,
                "renewables_mismatches": renewable_mismatches,
            },
        )
    )
    recomputed = data[PRIMARY_GENERATION_COLUMNS].sum(axis=1, min_count=1)
    generation_mix_mismatches = int(
        (~(
            data["generation_mix_mw"].eq(recomputed)
            | (data["generation_mix_mw"].isna() & recomputed.isna())
        )).sum()
    )
    checks.append(
        _check(
            "generation_mix_arithmetic",
            generation_mix_mismatches == 0,
            {"generation_mix_mismatches": generation_mix_mismatches},
        )
    )

    excluded_tokens = ("pumped", "battery_storage", "other_storage", "unknown_storage")
    accidentally_included = [
        column for column in data.columns if any(token in column for token in excluded_tokens)
    ]
    checks.append(
        _check(
            "standalone_and_pumped_storage_excluded",
            not accidentally_included,
            accidentally_included,
        )
    )

    provenance_results = {}
    manifest_files = {entry["filename"]: entry for entry in manifest["files"]}
    for filename, source in ARCHIVES.items():
        raw_path = RAW_DATA_DIR / filename
        entry = manifest_files.get(filename, {})
        provenance_results[filename] = {
            "exists": raw_path.exists(),
            "md5_matches_published": (
                raw_path.exists()
                and file_hash(raw_path, "md5") == source["published_md5"]
                and entry.get("published_md5") == source["published_md5"]
            ),
            "sha256_matches_manifest": (
                raw_path.exists() and file_hash(raw_path) == entry.get("sha256")
            ),
        }
    checks.append(
        _check(
            "raw_archive_integrity",
            all(all(result.values()) for result in provenance_results.values()),
            provenance_results,
        )
    )
    checks.append(
        _check(
            "versioned_provenance",
            manifest.get("zenodo_record_id") == ZENODO_RECORD_ID
            and manifest.get("zenodo_record_version") == ZENODO_RECORD_VERSION,
            {
                "zenodo_record_id": manifest.get("zenodo_record_id"),
                "zenodo_record_version": manifest.get("zenodo_record_version"),
            },
        )
    )

    report = {
        "passed": all(check["passed"] for check in checks),
        "checks_passed": sum(check["passed"] for check in checks),
        "checks_total": len(checks),
        "checks": checks,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    result = validate_data()
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)
