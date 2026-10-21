"""Shared configuration for the EIA-930 data pipeline."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

YEAR = 2025
BALANCING_AUTHORITIES = ("CISO", "ERCO", "NYIS", "PJM")

ZENODO_RECORD_ID = "23450617"
ZENODO_RECORD_VERSION = "97.0.0"
ZENODO_RECORD_URL = f"https://zenodo.org/records/{ZENODO_RECORD_ID}"
ZENODO_API_URL = f"https://zenodo.org/api/records/{ZENODO_RECORD_ID}"

ARCHIVES = {
    "eia930-2025half1.zip": {
        "url": (
            f"{ZENODO_API_URL}/files/eia930-2025half1.zip/content"
        ),
        "published_md5": "44e8f0a994c413571e2c18bb23771455",
    },
    "eia930-2025half2.zip": {
        "url": (
            f"{ZENODO_API_URL}/files/eia930-2025half2.zip/content"
        ),
        "published_md5": "48cf49085d90c80c60d9fd38a65caa49",
    },
}

RAW_MANIFEST_PATH = RAW_DATA_DIR / "provenance.json"
PROCESSED_DATA_PATH = PROCESSED_DATA_DIR / "eia930_2025_hourly.parquet"
METRICS_PATH = PROCESSED_DATA_DIR / "metrics_2025.json"
DATA_QUALITY_PATH = PROCESSED_DATA_DIR / "data_quality_2025.json"
VALIDATION_PATH = PROCESSED_DATA_DIR / "validation_2025.json"
