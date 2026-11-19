"""Fetch the Swiss Ephemeris data files the production build runs on.

    python tools/fetch_ephe.py

Writes `ephe/sepl_18.se1` (planets), `ephe/semo_18.se1` (Moon) and
`ephe/seas_18.se1` (main asteroids) -- the 1800-2399 CE files, which cover the
whole 2026 and 2027 spans. `ephe/` is gitignored: these are third-party data,
not project source. `finastro/ephem.py` picks the directory up automatically
(SE_EPHE_PATH, if set, wins), and every record's `qa.ephemeris` and the file's
`meta.ephemeris_backend` say which backend actually ran.

Each file is pinned by sha256, so a corrupted or substituted download fails
loudly instead of silently changing every minute in the calendar.
"""
from __future__ import annotations

import hashlib
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "ephe"
BASE = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe/"

FILES = {
    "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
    "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
    "seas_18.se1": "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2",
}


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    DEST.mkdir(exist_ok=True)
    bad = 0
    for name, want in FILES.items():
        path = DEST / name
        if not (path.exists() and _sha(path) == want):
            with urllib.request.urlopen(BASE + name, timeout=60) as r:
                path.write_bytes(r.read())
        got = _sha(path)
        ok = got == want
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {name}  {got}")
        if not ok:
            path.unlink()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
