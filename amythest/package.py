"""Package reader/writer for Amythest modules (.apkg)."""

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path
from typing import Dict, Optional, Union

from amythest.types import ModuleManifest


class ApkgError(Exception):
    pass


REQUIRED_FILES = ["manifest.json"]


def read_apkg(path: Union[str, Path]) -> Dict[str, object]:
    source = Path(path)
    if not source.exists():
        raise ApkgError(f"Module package not found: {source}")
    if not zipfile.is_zipfile(source):
        raise ApkgError(f"Not a valid .apkg zip archive: {source}")

    out: Dict[str, object] = {"manifest": None, "files": {}, "root": source}
    with zipfile.ZipFile(source, "r") as zf:
        namelist = zf.namelist()
        missing = [f for f in REQUIRED_FILES if f not in namelist]
        if missing:
            raise ApkgError(f"Missing required files in package: {missing}")
        raw = zf.read("manifest.json").decode("utf-8")
        out["manifest"] = ModuleManifest.from_json(raw)
        for name in namelist:
            if name == "manifest.json":
                continue
            out["files"][name] = zf.read(name)
    return out


def write_apkg(
    path: Union[str, Path],
    manifest: ModuleManifest,
    files: Optional[Dict[str, bytes]] = None,
) -> Path:
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    files = files or {}
    if "manifest.json" in files:
        raise ApkgError("Do not include manifest.json in files; pass manifest explicitly.")
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("manifest.json", manifest.to_json())
        for name, data in files.items():
            zf.writestr(name, data)
    return dest


def sha256_file(path: Union[str, Path]) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
