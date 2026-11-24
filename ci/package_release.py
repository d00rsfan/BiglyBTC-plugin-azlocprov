#!/usr/bin/env python3
"""Prepare an azlocprov asset and catalogue entry for offline release signing."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

UPSTREAM = "8e8224030ac772fcc8fcb22e80954342d6a66be1"
REPOSITORY = "d00rsfan/BiglyBTC-plugin-azlocprov"


def package(module, version_file, output):
    version = version_file.read_text().strip()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+\.[1-9][0-9]*", version):
        raise ValueError("Expected the numeric native CI version")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Expected an immutable source revision")
    data = module.read_bytes()
    if len(data) < 64 or data[:6] != b"\x7fELF\x02\x01" or int.from_bytes(data[18:20], "little") != 62:
        raise ValueError("Expected a Linux amd64 shared object")
    dynamic = subprocess.check_output(["readelf", "-d", module], text=True, timeout=20)
    if re.search(r"\((?:RPATH|RUNPATH)\)", dynamic):
        raise ValueError("Release module retains a runtime search path")
    identity = {"id": "azlocprov", "version": version, "platform": "linux-amd64",
                "nativeCommit": revision, "upstreamCommit": UPSTREAM}
    manifest = dict(identity, schema=1, hostAbi=1, moduleBytes=len(data),
                    moduleSha256=hashlib.sha256(data).hexdigest())
    leaf = "azlocprov-linux-amd64.tar.zst"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="plugin-release-", dir=output) as temporary:
        raw = Path(temporary) / "archive.tar"
        with tarfile.open(raw, "w", format=tarfile.PAX_FORMAT) as archive:
            for name, contents in (("manifest.json", json.dumps(manifest, sort_keys=True).encode()),
                                   ("plugin.so", data)):
                info = tarfile.TarInfo(name)
                info.size = len(contents)
                info.mode = 0o444
                archive.addfile(info, io.BytesIO(contents))
        asset = Path(temporary) / leaf
        subprocess.run(["zstd", "-q", "-T1", raw, "-o", asset], check=True, timeout=30)
        subprocess.run(["zstd", "-q", "-t", asset], check=True, timeout=30)
        asset_bytes = asset.read_bytes()
        asset.replace(output / leaf)
    entry = dict(identity, qt="6.12.0", minHostApi=1, maxHostApi=1, minHostAbi=1, maxHostAbi=1,
                 bytes=len(asset_bytes), sha256=hashlib.sha256(asset_bytes).hexdigest(),
                 url=f"https://github.com/{REPOSITORY}/releases/download/v{version}/{leaf}")
    (output / "catalogue-entry.json").write_text(json.dumps(entry, indent=2) + "\n")
    (output / "SHA256SUMS").write_text(f'{entry["sha256"]}  {leaf}\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("module", type=Path)
    parser.add_argument("version", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    package(args.module, args.version, args.output)
