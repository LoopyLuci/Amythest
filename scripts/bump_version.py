from __future__ import annotations

import re
import sys
from pathlib import Path

bump = sys.argv[1]
path = Path("pyproject.toml")
text = path.read_text(encoding="utf-8")
match = re.search(r'version = "(?P<version>\d+\.\d+\.\d+)"', text)
if not match:
    raise RuntimeError("version not found in pyproject.toml")
current = match.group("version")
major, minor, patch = current.split(".")
if bump == "major":
    major = str(int(major) + 1)
    minor = "0"
    patch = "0"
elif bump == "minor":
    minor = str(int(minor) + 1)
    patch = "0"
else:
    patch = str(int(patch) + 1)
next_version = f"{major}.{minor}.{patch}"
text = text[:match.start()] + f'version = "{next_version}"' + text[match.end():]
path.write_text(text, encoding="utf-8")
print(f"bumped {current} -> {next_version}")
