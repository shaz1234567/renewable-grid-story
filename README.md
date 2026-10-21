# The Renewable Grid, Hour by Hour

A single-page Plotly Dash story built from 2025 EIA-930 hourly operating data for CISO, ERCO, NYIS, and PJM. Six linked sections move from one day’s generation mix to source rhythms, annual patterns, regional comparison, variability, and renewable portfolio effects.

## Run locally

Python 3.11–3.13 is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8050`. For a production-style local process:

```bash
gunicorn app:server
```

## Test

```bash
pytest
python -c "import app; assert app.server"
```

## Data and methods

The app reads `data/processed/eia930_2025_hourly.parquet`; it does not rebuild or alter the data pipeline. Each record is an hourly average in MW. A sum across one-hour records is MWh, while charts described as daily means use arithmetic means of the available hourly observations.

Primary renewables are solar (with and without integrated battery storage), wind (with and without integrated battery storage), and hydropower excluding pumped storage. The generation-mix view also includes coal, natural gas, nuclear, petroleum, geothermal, and other reported generation. Missing values remain gaps and are disclosed beside each chart. Normalized charts divide a series by its own selected-period peak, so they compare shape rather than system size.

Map points are approximate reference locations for orientation and do not represent balancing-authority boundaries. Coefficient of variation is sample standard deviation divided by the absolute mean; it is explicitly undefined for zero or unavailable means.

## Deployment configuration

`render.yaml` documents a Render-compatible Gunicorn service, but no external deployment is performed by this project.
