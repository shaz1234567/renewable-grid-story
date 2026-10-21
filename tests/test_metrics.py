import pandas as pd

from src.data.metrics import compute_metrics


def test_metrics_sum_hourly_mw_as_mwh(tmp_path):
    input_path = tmp_path / "hourly.parquet"
    output_path = tmp_path / "metrics.json"
    pd.DataFrame(
        {
            "balancing_authority": ["CISO", "CISO"],
            "data_date": pd.to_datetime(["2025-01-01", "2025-01-01"]),
            "timestamp_utc": pd.to_datetime(
                ["2025-01-01T09:00Z", "2025-01-01T10:00Z"], utc=True
            ),
            "coal_mw": [0.0, 0.0],
            "natural_gas_mw": [0.0, 0.0],
            "nuclear_mw": [0.0, 0.0],
            "petroleum_mw": [0.0, 0.0],
            "geothermal_mw": [0.0, 0.0],
            "other_mw": [0.0, 0.0],
            "unknown_mw": [0.0, 0.0],
            "solar_mw": [10.0, 20.0],
            "wind_mw": [5.0, 7.0],
            "hydro_mw": [2.0, 3.0],
            "renewables_mw": [17.0, 30.0],
            "generation_mix_mw": [17.0, 30.0],
            "net_generation_mw": [50.0, 50.0],
        }
    ).to_parquet(input_path)

    result = compute_metrics(input_path, output_path)
    ciso = result["by_balancing_authority"]["CISO"]

    assert ciso["solar_mwh"] == 30
    assert ciso["renewables_mwh"] == 47
    assert ciso["renewable_share_of_net_generation_pct"] == 47
    assert output_path.exists()
