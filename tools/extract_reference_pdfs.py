"""Extract the two image-only reference PDFs into browsable HTML.

    python tools/extract_reference_pdfs.py [--cache DIR]

Writes Reference_materials/extracted/:
  index.html
  TA_Tech_Astro_Analysis_2020.html     265 pages
  KD_Parth_Prophecies_2026.html        223 pages
  img/ta/NNN.jpg, img/kd/NNN.jpg       page images (greyscale; book 1000 px, slides 1500 px wide)
  TA_verified_transcriptions.md        table transcriptions checked against the page images

Each page carries: the page image (the authoritative copy), a VERIFIED
transcription where the page's table was read from the image and checked, and
the machine OCR text (Tesseract 5; book pages --psm 6, slides --psm 3), which
is searchable but can contain errors, worst in tables and charts.

Needs pdftoppm and tesseract only if the cache lacks a page.
"""
from __future__ import annotations

import argparse
import html
import pathlib
import re
import subprocess
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
SRC = ROOT / "Reference_materials"
OUT = SRC / "extracted"
TA_PDF = SRC / "Tech Astro Analysis pages 1 to 265 all final new printout cq 10 2 2020.pdf"
KD_PDF = SRC / "KD Final PPT PDF 2026.pdf"

NOISE = re.compile(r"(Disclaimer|These are my studies|No recommendation to trade|PARTH PROPH|TECH.?ASTRO ANALY|Parth Proph)", re.I)


def page_assets(pdf, cache: pathlib.Path, n: int, psm: int, ocr_dir: str):
    """(png path, ocr text) for page n, rendering/OCR-ing into the cache if needed."""
    stem = f"{n:03d}"
    png = cache / ("tao" if "Tech" in pdf.name else "kdo") / f"{stem}.png"
    txt = cache / ocr_dir / f"{stem}.txt"
    if not png.exists():
        png.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["pdftoppm", "-r", "150", "-gray", "-png", "-f", str(n), "-l", str(n), "-singlefile", str(pdf), str(png.with_suffix(""))], check=True)
    if not txt.exists():
        txt.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["tesseract", str(png), str(txt.with_suffix("")), "--psm", str(psm)], check=True, capture_output=True)
    return png, txt.read_text(encoding="utf-8", errors="replace")


def clean(text: str) -> str:
    lines = [l.rstrip() for l in text.splitlines()]
    lines = [l for l in lines if l.strip() and not NOISE.search(l)]
    return "\n".join(lines)


def jpg(png: pathlib.Path, dest: pathlib.Path, w: int = 1000):
    if dest.exists():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    im = Image.open(png).convert("L")
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    im.save(dest, "JPEG", quality=55, optimize=True, progressive=True)


# ------------------------------------------------------------ verified text
def ta_verified() -> dict:
    """page -> list of verified transcription blocks."""
    out: dict = {}
    md = (OUT / "TA_verified_transcriptions.md").read_text(encoding="utf-8").splitlines()
    cur = None
    for line in md[1:]:
        m = re.match(r"p(\d+)(?:-(\d+))?\b(.*)", line)
        if m:
            a, b = int(m.group(1)), int(m.group(2) or m.group(1))
            cur = list(range(a, b + 1))
            for p in cur:
                out.setdefault(p, []).append(line)
        elif cur and line.strip():
            for p in cur:
                out[p][-1] += "\n" + line
    # Section 25 relationship tables and the Vedha wheel, from the catalogue data
    from finastro.pdfref import catalogue as C, vedha as V
    REL = {1: "Together", 7: "7th to each other", 6: "6/8 to each other", 5: "5/9 to each other",
           3: "3/11 to each other", 2: "2/12 to each other", 4: "4/10 to each other"}
    for (a, b, page), tab in C.S25.items():
        rows = "\n".join(f"  {REL[k]}: {v}" for k, v in tab.items())
        out.setdefault(page, []).append(f"S25 {C.name(a).upper()} WITH {C.name(b).upper()}\n{rows}")
    wheel = "\n".join(f"  {k}: South/Right {v[0]} | East/Left {v[1]} | Front {v[2]}" for k, v in V.TA_WHEEL.items())
    out.setdefault(131, []).append("VEDHA wheel (all 28 rows, pp.131-133):\n" + wheel)
    return out


KD_VERIFIED = {
    27: "Transit Warning: Mars to Saturn Dwidwadash Yog - high bearish potential due to Mars-Saturn axis and Mars-Rahu conjunction. Mars transit 12th (Aquarius) to Saturn (Pisces) forms Dwidwadash Yog; Mars and Rahu conjunct in the same sign; Mars is Atichari in this period; Jupiter applies 9th aspect on Rahu - protective influence that can limit damage. Net outlook: elevated negativity but damage may be manageable.",
    32: "High-probable turning events: Hemisphere dates (twice a year; the chart pages 37-70 date them at the equinoxes, 'North Hemisphere' ~20-21 March, 'South Hemisphere' ~22-23 September); Sun-Neptune conjunction (once a year); Mercury retrograde (usually three times a year).",
    33: "Sun-Mercury conjunction: occurs 6-7 times a year.",
    34: "Mercury-Venus conjunction 3/4 times a year - include as a potential turning event. Total Day - date plus month sum equals last two digits of year; occurs twelve times a year; treat as checklist item.",
    83: "When Malefic Planets Transit a Nakshtra: Expect Sector-Specific Rallies - rallies linked to the Nakshtra lord's sectors.",
    86: "Mars at 28 deg in any Sign - Can Reverse or Intensify Trends. Context: listed under Principles of Financial Astrology Book, page 79. Reference: Point No 39 in the Many Important Observation.",
    87: "Mars in Dhanistha: Immediate Bearish.",
    94: ("SHANI CHANDRA DWIDWADASH YOG - BEARISH (2026), START DATE | START TIME | END DATE | END TIME | SIGN:\n"
         "21-Jan-26 1:37 | 23-Jan-26 8:34 | Aquarius\n17-Feb-26 9:06 | 19-Feb-26 15:01 | Aquarius\n16-Mar-26 18:15 | 18-Mar-26 23:36 | Aquarius\n"
         "13-Apr-26 3:45 | 15-Apr-26 9:38 | Aquarius\n10-May-26 12:13 | 12-May-26 19:25 | Aquarius\n06-Jun-26 19:05 | 09-Jun-26 3:37 | Aquarius\n"
         "04-Jul-26 0:49 | 06-Jul-26 9:58 | Aquarius\n31-Jul-26 6:39 | 02-Aug-26 15:28 | Aquarius\n27-Aug-26 13:36 | 29-Aug-26 21:38 | Aquarius\n"
         "23-Sep-26 21:57 | 26-Sep-26 5:34 | Aquarius\n21-Oct-26 7:01 | 23-Oct-26 15:04 | Aquarius\n17-Nov-26 15:31 | 20-Nov-26 0:50 | Aquarius\n"
         "14-Dec-26 22:36 | 17-Dec-26 9:13 | Aquarius\n"
         "Bottom: HIGHEST IMPACT SEEN TILL MOON REACHES THE DEGREE OF SATURN. THIS YEAR SHANI CHANDRA DWIDWADASH YOG WILL BE HAPPENING IN THE AQUARIUS PISCES AXIS WHICH IS INAUSPICIOUS, SO HIGH NEGATIVITY MAYBE SEEN."),
    134: "Lunar Eclipse Patterns and Market Biases: Moon eclipse on Tuesday - Bullish; Moon eclipse in Vaishakh, Shravan or Ashvin month - Bullish; Moon eclipse in Jyeshtha or Paush month - Bearish then Bullish; Moon eclipse in Margashirsh month - Bearish; Moon and Mercury together in D9 chart - Bullish; Mars or Rahu in Virgo sign - Bullish.",
    135: "Mars and Planetary Interactions: 1 Atichari (very fast moving) Mars in Capricorn - Bearish; 2 Jupiter crosses Mars in same sign - Bearish; 3 Mars crosses Jupiter - Bullish for eleven days; 4 Mars at 28 degrees in any sign - trend reversal or intensification; 5 Mars and Saturn together in Aries; Venus joins them - Bearish reversal; 6 Mars and Venus together in Gemini - High Bullish; 7 Mars and Venus in same Nakshatra - Bullish.",
    136: "Mars Transit: Immediate Market Signals - Mars in Rohini or Chitra - Bullish (supports positive momentum); Mars in Vishakha Nakshatra - Immediate (expect near-term upside); Mars in Dhanistha - Immediate Bearish; Mars in Purva Bhadrapad - Bullish after 3 to 4 days (delayed positive impact); Atichari Mars in Purva Bhadrapad - Bearish (accelerated transit flips sentiment); Mars in Pisces in D9 - Bearish.",
    142: "Saturn Transit Signals: 1 Saturn enters Uttra Shada - Bullish after 3 days; 2 Saturn retrograde in Vishakha - 27 days bullish; 3 Saturn in Uttra Bhadrapad - High bullish; 4 Retrograde Saturn goes combust - Bearish; 5 Retrograde Saturn in Ashwini or Bharani - High bullish in commodities; 6 Saturn retrograde on Magha then enters Ashlesha - High bullish for markets; 7 Retrograde Saturn on Jyeshtha enters Anuradha - High bullish for market (July - August 2016); 8 Retrograde Saturn on Uttara Shada enters Purva Shada - High bullish for markets.",
}

CSS = """:root{--bg:#fbfaf7;--fg:#1d1d1f;--mut:#6b6b70;--line:#e3e1db;--card:#fff;--ok:#1f6f4a;--okbg:#eef7f1}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#151517;--fg:#ececee;--mut:#a0a0a8;--line:#2c2c30;--card:#1d1d20;--ok:#7fd3a6;--okbg:#17271f}}
:root[data-theme=dark]{--bg:#151517;--fg:#ececee;--mut:#a0a0a8;--line:#2c2c30;--card:#1d1d20;--ok:#7fd3a6;--okbg:#17271f}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;margin:0;padding:16px;max-width:1500px;margin:auto}
h1{font-size:22px;margin:0 0 6px}p.m{color:var(--mut);max-width:75em}a{color:inherit}
nav{columns:3 18em;font-size:13px;border:1px solid var(--line);background:var(--card);padding:10px 14px;border-radius:8px}
nav a{display:block;text-decoration:none;padding:1px 0}nav a:hover{text-decoration:underline}
.bar{position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:2;display:flex;gap:8px;flex-wrap:wrap}
input{font:inherit;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);min-width:18em}
section{border-top:1px solid var(--line);padding:14px 0;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}
section h2{grid-column:1/-1;font-size:16px;margin:0}section h2 small{color:var(--mut);font-weight:400}
img{width:100%;height:auto;border:1px solid var(--line);border-radius:4px;background:#fff}
.v{background:var(--okbg);border-left:3px solid var(--ok);padding:6px 10px;margin:0 0 10px;white-space:pre-wrap;font-size:13px}
.v b{color:var(--ok)}pre{white-space:pre-wrap;font:12.5px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace;margin:0;color:var(--fg)}
details summary{cursor:pointer;color:var(--mut);font-size:13px}
@media (max-width:800px){section{grid-template-columns:1fr}}"""

JS = """const q=document.getElementById('q');q.oninput=()=>{const v=q.value.toLowerCase();
for(const s of document.querySelectorAll('section')){s.style.display=!v||s.textContent.toLowerCase().includes(v)?'':'none'}};"""


def title_of(text: str) -> str:
    for l in text.splitlines():
        l2 = re.sub(r"[^A-Za-z0-9&/(),.'\- ]", "", l).strip()
        if len(re.sub(r"[^A-Za-z]", "", l2)) >= 8:
            return l2[:90]
    return ""


def build(doc, pdf, pages, cache, psm, ocr_dir, verified, printed, tag, fname, intro):
    secs, nav = [], []
    for n in range(1, pages + 1):
        png, txt = page_assets(pdf, cache, n, psm, ocr_dir)
        jpg(png, OUT / "img" / tag / f"{n:03d}.jpg", 1500 if tag == "kd" else 1000)
        text = clean(txt)
        head = title_of(text)
        pr = printed(n)
        ver = verified.get(n, [])
        if isinstance(ver, str):
            ver = [ver]
        vhtml = "".join(f"<div class='v'><b>Verified transcription</b> (read from the page image)\n{html.escape(v)}</div>" for v in ver)
        nav.append(f"<a href='#p{n:03d}'>{n:03d} {html.escape(head)}</a>")
        secs.append(f"<section id='p{n:03d}'><h2>PDF page {n}{f' <small>(printed page {pr})</small>' if pr else ''} &mdash; {html.escape(head)}</h2>"
                    f"<div><a href='img/{tag}/{n:03d}.jpg' target='_blank'><img loading='lazy' src='img/{tag}/{n:03d}.jpg' alt='PDF page {n}'></a></div>"
                    f"<div>{vhtml}<details{' open' if not ver else ''}><summary>Machine OCR text (Tesseract; may contain errors - the image is authoritative)</summary><pre>{html.escape(text) or '(no text recognised - image only)'}</pre></details></div></section>")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(doc)}</title><style>{CSS}</style></head><body>
<h1>{html.escape(doc)}</h1><p class="m">{intro} Source: <code>Reference_materials/{html.escape(pdf.name)}</code> ({pages} pages). <a href="index.html">All extracted documents</a>.</p>
<details><summary>Contents (first legible line of each page)</summary><nav>{''.join(nav)}</nav></details>
<div class="bar"><input id="q" placeholder="Search all pages (OCR + verified text)"></div>
{''.join(secs)}<script>{JS}</script></body></html>"""
    (OUT / fname).write_text(page, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=str(ROOT / "build" / "ocr_cache"))
    a = ap.parse_args()
    cache = pathlib.Path(a.cache)
    OUT.mkdir(parents=True, exist_ok=True)
    build("Tech Astro Analysis (2020) - extracted", TA_PDF, 265, cache, 6, "tao", ta_verified(),
          lambda n: n - 30 if 31 <= n <= 168 else None, "ta", "TA_Tech_Astro_Analysis_2020.html",
          "Parth Prophesies, 'Tech Astro Analysis' 2020 edition. Lessons pp.40-168 (Sections 3-37), 2020 ephemeris tables pp.169-244, 2020 story & technical corner pp.245-265.")
    build("KD - Parth Prophecies, Argh Martand 2026 deck - extracted", KD_PDF, 223, cache, 3, "kd3", KD_VERIFIED,
          lambda n: None, "kd", "KD_Parth_Prophecies_2026.html",
          "Slides: 2016-2032 transit review pp.5-22; method & turning dates pp.23-35; turning-date charts pp.36-81; 2026 prophecies pp.82-128; rule slides pp.129-148; sector outperformance, technical learning and gold/macro pp.149-223.")
    (OUT / "index.html").write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reference PDFs extracted</title><style>{CSS}</style></head><body><h1>Reference PDFs - extracted</h1>
<p class="m">Both PDFs are image-only scans. Each page below has its image, the machine OCR text, and - where the page's table was read from the image and checked - a verified transcription. Built by <code>tools/extract_reference_pdfs.py</code>.</p>
<ul><li><a href="TA_Tech_Astro_Analysis_2020.html">Tech Astro Analysis (2020), 265 pages</a></li>
<li><a href="KD_Parth_Prophecies_2026.html">KD - Parth Prophecies / Argh Martand 2026 deck, 223 pages</a></li>
<li><a href="TA_verified_transcriptions.md">TA verified table transcriptions (Markdown)</a></li>
<li>Rules implemented from both: <code>finastro/pdfref/catalogue.py</code>; rule list and conflicts: <code>build/pdfref/REFERENCE_PDF_RULES.md</code></li></ul></body></html>""", encoding="utf-8")
    print("done")


if __name__ == "__main__":
    main()
