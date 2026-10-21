"""Download the versioned 2025 EIA-930 bulk archives with provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from src.config import (
    ARCHIVES,
    RAW_DATA_DIR,
    RAW_MANIFEST_PATH,
    ZENODO_RECORD_ID,
    ZENODO_RECORD_URL,
    ZENODO_RECORD_VERSION,
)

CHUNK_SIZE = 1024 * 1024


def file_hash(path: Path, algorithm: str = "sha256") -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_file(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "renewable-grid-story/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
            while chunk := response.read(CHUNK_SIZE):
                output.write(chunk)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def download_archives(force: bool = False) -> dict:
    """Download archives, verify the published MD5, and write SHA-256 provenance."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    files = []
    for filename, source in ARCHIVES.items():
        path = RAW_DATA_DIR / filename
        if force or not path.exists():
            download_file(source["url"], path)

        md5 = file_hash(path, "md5")
        if md5 != source["published_md5"]:
            raise ValueError(
                f"MD5 mismatch for {filename}: expected {source['published_md5']}, got {md5}"
            )
        files.append(
            {
                "filename": filename,
                "source_url": source["url"],
                "bytes": path.stat().st_size,
                "published_md5": source["published_md5"],
                "verified_md5": md5,
                "sha256": file_hash(path),
            }
        )

    manifest = {
        "dataset": "EIA Form 930 Hourly and Daily Balancing Authority Operations Report",
        "provider": "U.S. Energy Information Administration",
        "archive_publisher": "Catalyst Cooperative / PUDL",
        "zenodo_record_id": ZENODO_RECORD_ID,
        "zenodo_record_version": ZENODO_RECORD_VERSION,
        "zenodo_record_url": ZENODO_RECORD_URL,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": files,
    }
    RAW_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="replace existing archives")
    args = parser.parse_args()
    manifest = download_archives(force=args.force)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
