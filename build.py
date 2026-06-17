#!/usr/bin/env python3
"""Build Kodi-installable zips for both addons into dist/.

For each addon the version is read from its addon.xml, so a version bump there is
picked up automatically. Each zip has the addon-id folder at its root
(``<addon-id>/addon.xml``), which is what Kodi's "Install from zip file" expects.

Usage:  python3 build.py
Output: dist/<addon-id>-<version>.zip
"""
import os
import re
import zipfile

ADDONS = ["script.module.python.twitch", "plugin.video.twitch"]
EXCLUDE_DIRS = {"__pycache__", "addon_data", ".git"}
ROOT = os.path.dirname(os.path.abspath(__file__))


def addon_version(addon_dir):
    with open(os.path.join(addon_dir, "addon.xml"), encoding="utf-8") as fh:
        head = fh.read(2000)
    m = re.search(r'<addon\b[^>]*\bversion="([^"]+)"', head)
    if not m:
        raise SystemExit(f"no version found in {addon_dir}/addon.xml")
    return m.group(1)


def build(addon):
    base = os.path.join(ROOT, addon)
    version = addon_version(base)
    dist = os.path.join(ROOT, "dist")
    os.makedirs(dist, exist_ok=True)
    out = os.path.join(dist, f"{addon}-{version}.zip")
    if os.path.exists(out):
        os.remove(out)
    count = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for f in files:
                if f.endswith((".pyc", ".pyo")):
                    continue
                full = os.path.join(dirpath, f)
                rel = os.path.relpath(full, ROOT)  # -> "<addon-id>/..."
                z.write(full, rel)
                count += 1
    print(f"{addon} {version}: {count} files -> dist/{os.path.basename(out)}")


if __name__ == "__main__":
    for a in ADDONS:
        build(a)
