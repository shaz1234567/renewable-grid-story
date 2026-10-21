import hashlib
import json

import pandas as pd

import src.data.validate as validate


def test_validation_reports_coverage_gaps_and_preserves_arithmetic_checks(
    tmp_path, monkeypatch
):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raw_path = raw_dir / "one.zip"
    raw_path.write_bytes(b"archive")
    md5 = hashlib.md5(b"archive").hexdigest()
    sha256 = hashlib.sha256(b"archive").hexdigest()

    manifest_path = raw_dir / "provenance.json"
    manifest_path.write_text(
        json.dumps(
            {
                "zenodo_record_id": validate.ZENODO_RECORD_ID,
                "zenodo_record_version": validate.ZENODO_RECORD_VERSION,
                "files": [
                    {
                        "filename": "one.zip",
                        "published_md5": md5,
                        "sha256": sha256,
                    }
                ]
            }
        )
    )
    frame = pd.DataFrame(
        {
            "balancing_authority": ["CISO", "CISO"],
            "data_date": pd.to_datetime(["2025-01-01", "2025-01-01"]),
            "timestamp_utc": pd.to_datetime(
                ["2025-01-01T09:00Z", "2025-01-01T11:00Z"], utc=True
            ),
            "demand_mw": [100.0, 100.0],
            "net_generation_mw": [90.0, 90.0],
            "coal_mw": [0.0, 0.0],
            "natural_gas_mw": [0.0, 0.0],
            "nuclear_mw": [0.0, 0.0],
            "petroleum_mw": [0.0, 0.0],
            "geothermal_mw": [0.0, 0.0],
            "other_mw": [0.0, 0.0],
            "unknown_mw": [0.0, 0.0],
            "solar_without_battery_mw": [10.0, 10.0],
            "solar_with_battery_mw": [2.0, 2.0],
            "wind_without_battery_mw": [20.0, 20.0],
            "wind_with_battery_mw": [3.0, 3.0],
            "solar_mw": [12.0, 12.0],
            "wind_mw": [23.0, 23.0],
            "hydro_mw": [5.0, 5.0],
            "renewables_mw": [40.0, 40.0],
            "generation_mix_mw": [40.0, 40.0],
        }
    )
    input_path = tmp_path / "data.parquet"
    frame.to_parquet(input_path)

    monkeypatch.setattr(validate, "ARCHIVES", {"one.zip": {"published_md5": md5}})
    monkeypatch.setattr(validate, "RAW_DATA_DIR", raw_dir)
    report = validate.validate_data(
        input_path, manifest_path, tmp_path / "validation.json"
    )
    checks = {check["name"]: check for check in report["checks"]}

    assert report["passed"] is False
    assert checks["continuous_hourly_utc"]["passed"] is False
    assert checks["renewable_category_arithmetic"]["passed"] is True
    assert checks["raw_archive_integrity"]["passed"] is True
