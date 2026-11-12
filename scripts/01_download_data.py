"""Download the Afrobarometer Round 10 Nigeria data file into data/raw/.

    python scripts/01_download_data.py

Nothing is changed: the file is saved exactly as published, and its size and
SHA-256 are written to data/raw/manifest.json so anyone can confirm they are
working from the same file.

Source: Afrobarometer Data, Nigeria, Round 10, 2024. https://www.afrobarometer.org
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
FILES = {
    "nigeria_r10_2024.sav": "https://www.afrobarometer.org/wp-content/uploads/2025/11/"
                            "NIG_R10.Data_18Nov24.wtd_.final_.release_updated.13Feb25.sav",
}


def fetch(url: str, target: Path) -> None:
    """Stream one file to disk, retrying on network errors."""
    for attempt in range(6):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; portfolio-analysis/1.0)"})
            with urllib.request.urlopen(request, timeout=120) as response, target.open("wb") as handle:
                while chunk := response.read(1 << 20):
                    handle.write(chunk)
            return
        except Exception as error:  # noqa: BLE001 - any network failure is retried
            print(f"  retry {attempt + 1}: {type(error).__name__}: {error}", flush=True)
            time.sleep(5 + 5 * attempt)
    raise SystemExit(f"Could not download {url}")


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = {"retrieved_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "files": {}}
    for name, url in FILES.items():
        target = RAW / name
        if not target.exists():
            fetch(url, target)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        manifest["files"][name] = {"url": url, "bytes": target.stat().st_size, "sha256": digest}
        print(f"{name}: {target.stat().st_size / 1e6:.2f} MB  sha256 {digest[:16]}...")
    (RAW / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
