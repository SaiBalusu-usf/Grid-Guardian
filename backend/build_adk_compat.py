"""Reproduce the narrowly scoped ADK 2.13.0 telemetry compatibility wheel.

No upstream Python code or license is changed. Only the distribution version
and two telemetry requirements change. See SECURITY_MIGRATION.md.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

URL = "https://files.pythonhosted.org/packages/e8/1a/6da4a8048b7cd47681928daed5d4d1c3ef971b3847fcc3cbc63f94df39d2/google_adk-2.13.0-py3-none-any.whl"
SHA256 = "bec4c4ee0aa3e63a2243c23365c5aef666ea539bc48c78dfbbf004dbddfc5f00"
VERSION = "2.13.0+gridguardian.1"
OLD_INFO = "google_adk-2.13.0.dist-info"
NEW_INFO = f"google_adk-{VERSION}.dist-info"


def build(source: bytes, output: Path) -> None:
    if hashlib.sha256(source).hexdigest() != SHA256:
        raise ValueError("Upstream ADK wheel does not match the reviewed SHA-256")
    entries = {}
    with ZipFile(io.BytesIO(source)) as upstream:
        for name in upstream.namelist():
            if name.endswith("/RECORD"):
                continue
            data = upstream.read(name)
            if name == f"{OLD_INFO}/METADATA":
                metadata = data.decode("utf-8")
                replacements = {
                    "Version: 2.13.0\n": f"Version: {VERSION}\n",
                    "Requires-Dist: opentelemetry-api>=1.39,<=1.44\n":
                        "Requires-Dist: opentelemetry-api>=1.45.1,<1.46\n",
                    "Requires-Dist: opentelemetry-sdk>=1.39,<=1.44\n":
                        "Requires-Dist: opentelemetry-sdk>=1.45.1,<1.46\n",
                }
                for old, new in replacements.items():
                    if metadata.count(old) != 1:
                        raise ValueError("Unexpected upstream metadata; manual review required")
                    metadata = metadata.replace(old, new)
                data = metadata.encode("utf-8")
            entries[name.replace(OLD_INFO, NEW_INFO)] = data
    record = io.StringIO(newline="")
    writer = csv.writer(record, lineterminator="\n")
    for name, data in sorted(entries.items()):
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        writer.writerow([name, f"sha256={digest}", len(data)])
    writer.writerow([f"{NEW_INFO}/RECORD", "", ""])
    entries[f"{NEW_INFO}/RECORD"] = record.getvalue().encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as wheel:
        for name, data in sorted(entries.items()):
            info = ZipInfo(name, date_time=(2026, 10, 26, 0, 0, 0))
            # ZipInfo otherwise embeds the builder OS (Windows=0, Unix=3).
            info.create_system = 3
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            wheel.writestr(info, data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Previously downloaded, hash-verified upstream wheel")
    args = parser.parse_args()
    if args.source:
        source = args.source.read_bytes()
    else:
        with urlopen(URL, timeout=60) as response:
            source = response.read(25 * 1024 * 1024)
    output = Path(__file__).parent / "vendor" / f"google_adk-{VERSION}-py3-none-any.whl"
    build(source, output)
    print(f"Built {output.name}: sha256={hashlib.sha256(output.read_bytes()).hexdigest()}")
