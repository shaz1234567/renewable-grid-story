import hashlib

from src.data.download_eia930 import file_hash


def test_file_hash_supports_sha256_and_md5(tmp_path):
    path = tmp_path / "sample.bin"
    path.write_bytes(b"EIA-930")

    assert file_hash(path) == hashlib.sha256(b"EIA-930").hexdigest()
    assert file_hash(path, "md5") == hashlib.md5(b"EIA-930").hexdigest()
