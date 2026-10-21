from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd

import src.data.prepare as prepare


def test_prepare_prefers_adjusted_and_aggregates_only_primary_renewables(
    tmp_path, monkeypatch
):
    row = {column: None for column in prepare.INPUT_COLUMNS}
    row.update(
        {
            "Balancing Authority": "CISO",
            "Data Date": "01/01/2025",
            "Hour Number": 1,
            "Local Time at End of Hour": "01/01/2025 1:00:00 AM",
            "UTC Time at End of Hour": "01/01/2025 9:00:00 AM",
            "Region": "CAL",
        }
    )
    values = {
        "demand_mw": 100,
        "net_generation_mw": 90,
        "coal_mw": 5,
        "natural_gas_mw": 6,
        "nuclear_mw": 7,
        "petroleum_mw": 1,
        "hydro_mw": 3,
        "solar_without_battery_mw": 10,
        "solar_with_battery_mw": 2,
        "wind_without_battery_mw": 20,
        "wind_with_battery_mw": 4,
        "geothermal_mw": 8,
        "other_mw": 9,
        "unknown_mw": 10,
    }
    for output_name, value in values.items():
        adjusted, imputed, raw = prepare._variants(
            output_name, prepare.RAW_FIELDS[output_name]
        )
        row[raw] = value - 1
        row[imputed] = value - 0.5
        row[adjusted] = value

    archive_path = tmp_path / "one.zip"
    csv = pd.DataFrame([row]).to_csv(index=False)
    with ZipFile(archive_path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("eia930-test-balance.csv", csv)

    monkeypatch.setattr(prepare, "ARCHIVES", {"one.zip": {}})
    monkeypatch.setattr(prepare, "DATA_QUALITY_PATH", tmp_path / "quality.json")
    output, _ = prepare.prepare_data(tmp_path, tmp_path / "output.parquet")

    record = output.iloc[0]
    assert record["demand_mw"] == 100
    assert record["solar_mw"] == 12
    assert record["wind_mw"] == 24
    assert record["renewables_mw"] == 39
    assert record["coal_mw"] == 5
    assert record["natural_gas_mw"] == 6
    assert record["nuclear_mw"] == 7
    assert record["petroleum_mw"] == 1
    assert record["geothermal_mw"] == 8
    assert record["other_mw"] == 9
    assert record["unknown_mw"] == 10
    assert record["generation_mix_mw"] == 85
    assert not any("pumped" in column for column in output.columns)
