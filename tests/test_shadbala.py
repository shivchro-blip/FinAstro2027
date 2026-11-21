"""Shadbala / Ashtakavarga against B.V. Raman's worked example ('Graha and Bhava Balas').

Chart: 16 Oct 1918, 14:22:16 IST, 13N 77E35, Raman ayanamsa; expected values as printed
in the book. convention="raman" reproduces the book's own conventions (see shadbala.py).
"""
import datetime as dt
import pathlib
import sys

import swisseph as swe

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from finastro.pdfref import shadbala as S  # noqa: E402

IST = dt.timezone(dt.timedelta(hours=5.5))
P = S.PLANETS
BOOK = {
    "uchcha": [3.0, 32.75, 37.06, 54.5, 56.33, 1.95, 34.08],
    "saptavargaja": [90, 48.75, 90, 135, 71.25, 116.25, 97.5],
    "ojayugma": [30, 15, 15, 30, 15, 30, 15],
    "kendradi": [60, 30, 30, 60, 15, 15, 30],
    "drekkana": [15, 0, 0, 0, 0, 15, 0],
    "nathonnatha": [48.32, 11.68, 11.68, 60, 48.32, 48.32, 11.68],
    "paksha": [16.54, 86.92, 16.54, 16.54, 43.46, 43.46, 16.54],
    "tribhaga": [0, 0, 0, 0, 60, 0, 60],
    "abda": [0, 0, 0, 0, 0, 0, 15],
    "masa": [0, 0, 0, 30, 0, 0, 0],
    "dina": [0, 0, 0, 45, 0, 0, 0],
    "hora": [0, 60, 0, 0, 0, 0, 0],
    "drik": [15.86, -21.73, 0.95, 15.64, -16.04, 18.47, 7.21],
    "total": [424.24, 389.80, 306.20, 537.02, 433.71, 376.15, 389.21],
}


def chart():
    c = S.build_chart(dt.datetime(1918, 10, 16, 14, 22, 16, tzinfo=IST), 13.0, 77 + 35 / 60, ayanamsa=swe.SIDM_RAMAN)
    c.local_date = dt.date(1918, 10, 16)
    return c


def comp(r, k, p):
    x = r[p]
    if k in x["sthana"] and k != "total":
        return x["sthana"][k]
    if k in x["kala"] and k != "total":
        return x["kala"][k]
    return x[k]


def test_components_match_raman():
    r = S.shadbala(chart(), "raman")
    for k in ("uchcha", "saptavargaja", "ojayugma", "kendradi", "drekkana", "nathonnatha", "paksha",
              "tribhaga", "abda", "masa", "dina", "hora", "drik"):
        for p, e in zip(P, BOOK[k]):
            tol = 1.0 if k != "uchcha" else 0.8
            assert abs(comp(r, k, p) - e) <= tol, (k, p, comp(r, k, p), e)


def test_totals_match_raman():
    r = S.shadbala(chart(), "raman")
    for p, e in zip(P, BOOK["total"]):
        # Mars: the book's dig bala (64.30) exceeds the 60-virupa maximum (misprint); Mercury: cheshta epoch tables
        tol = 10 if p == "Mars" else 5 if p == "Mercury" else 1.5
        assert abs(r[p]["total"] - e) <= tol, (p, r[p]["total"], e)


def test_ashtakavarga_totals():
    bav, sav = S.ashtakavarga(chart())
    assert sum(sav) == 337
    assert {p: sum(v) for p, v in bav.items()} == {"Sun": 48, "Moon": 49, "Mars": 39, "Mercury": 54, "Jupiter": 56, "Venus": 52, "Saturn": 39}


def test_bphs_ahargana_example():
    # BPHS (Santhanam) p.270: 1 June 1984 -> abbreviated ahargana 65295, year opened Thursday, month Friday, day Friday
    A = S.ahargana(dt.date(1984, 6, 1))
    assert A == 65295
    assert S.WEEKDAY_LORD[(3 * (A // 360) + 1) % 7] == "Jupiter"
    assert S.WEEKDAY_LORD[(2 * (A // 30) + 1) % 7] == "Venus"
    assert S.WEEKDAY_LORD[A % 7] == "Venus"
